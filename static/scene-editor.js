// Scene Editor Module - extracted from app.js to keep core engine lean
// Attaches editor-specific methods to StoryEngine prototype

(function(){
  if (typeof StoryEngine === 'undefined') {
    console.error('Scene Editor module loaded before StoryEngine');
    return;
  }

  // --- Step 2: Minimal State & Event Bus -------------------------------------------------
  const sceneState = {
    current: null,
    blocks: [],
    entities: [],
    dirty: { scene: false, blocks: new Set() }
  };
  window.sceneState = sceneState; // expose for debugging

  const bus = {
    _e: {},
    on(evt, fn){ (this._e[evt] ||= new Set()).add(fn); return () => this.off(evt, fn); },
    off(evt, fn){ this._e[evt]?.delete(fn); },
    emit(evt, data){ this._e[evt]?.forEach(fn => { try { fn(data); } catch(e){ console.error('bus handler error', e);} }); }
  };
  window.sceneBus = bus; // for debugging

  // --- T5: Undo Stack System -------------------------------------------------
  const undoStack = {
    stack: [],
    maxSize: 10,
    
    // Push a new undo action onto the stack
    push(action) {
      this.stack.push(action);
      if (this.stack.length > this.maxSize) {
        this.stack.shift(); // Remove oldest action
      }
      this.updateUndoButton();
      console.debug('[T5] Undo action pushed:', action.type, this.stack.length);
    },
    
    // Pop and execute the last undo action
    async pop() {
      if (this.stack.length === 0) {
        updateGlobalStatus('Nothing to undo', 'warn');
        return false;
      }
      
      const action = this.stack.pop();
      this.updateUndoButton();
      
      try {
        updateGlobalStatus(`Undoing ${action.type}...`, 'loading');
        await this.executeUndo(action);
        updateGlobalStatus(`Undone: ${action.type}`, 'success');
        console.debug('[T5] Undo action executed:', action.type);
        return true;
      } catch (error) {
        console.error('[T5] Undo failed:', error);
        updateGlobalStatus(`Undo failed: ${error.message}`, 'error');
        return false;
      }
    },
    
    // Execute specific undo action
    async executeUndo(action) {
      switch (action.type) {
        case 'block-content':
          await this.undoBlockContent(action);
          break;
        case 'block-reorder':
          await this.undoBlockReorder(action);
          break;
        case 'block-delete':
          await this.undoBlockDelete(action);
          break;
        case 'block-create':
          await this.undoBlockCreate(action);
          break;
        default:
          throw new Error(`Unknown undo action type: ${action.type}`);
      }
    },
    
    // Undo block content change
    async undoBlockContent(action) {
      const blockEl = document.querySelector(`details[data-block-id="${action.blockId}"]`);
      if (!blockEl) throw new Error('Block not found');
      
      const blockType = blockEl.getAttribute('data-block-type');
      
      // Restore content in UI
      if (blockType === 'milestone') {
        const [subject, object] = action.previousContent.split(' ');
        blockEl.querySelector('input[placeholder*="Subject"]').value = subject || '';
        blockEl.querySelector('input[placeholder*="Object"]').value = object || '';
      } else if (blockType === 'dialogue') {
        // T9: Restore structured dialogue content
        // For now, restore as plain text content in the first line
        // More sophisticated restoration could parse speaker/content pairs
        const firstTextarea = blockEl.querySelector('.dialogue-content');
        if (firstTextarea) firstTextarea.value = action.previousContent;
      } else {
        const textarea = blockEl.querySelector('textarea');
        if (textarea) textarea.value = action.previousContent;
      }
      
      // Save to server
      await StoryEngine.prototype.saveBlock.call(window.storyEngine, action.blockId, blockEl);
    },
    
    // Undo block reorder operation
    async undoBlockReorder(action) {
      // Restore the original order by calling reorder API
      const reorderData = action.previousOrder.map((blockId, index) => ({ id: blockId, order: index }));
      
      // Update state
      sceneState.blocks = action.previousOrder.map(blockId => 
        sceneState.blocks.find(b => b.id === blockId)
      ).filter(Boolean);
      
      // Update DOM
      const container = document.getElementById('scene-content');
      const fragment = document.createDocumentFragment();
      action.previousOrder.forEach(blockId => {
        const blockEl = document.querySelector(`details[data-block-id="${blockId}"]`);
        if (blockEl) fragment.appendChild(blockEl);
      });
      container.appendChild(fragment);
      
      // Save order to server
      await window.storyEngine.reorderBlocks(reorderData);
    },
    
    // Undo block deletion by recreating it
    async undoBlockDelete(action) {
      // Recreate the block via API
      const response = await window.storyEngine.api.post(
        `/api/v1/scenes/${window.storyEngine.currentSceneId}/blocks`,
        action.blockData
      );
      
      const recreatedBlock = window.storyEngine.extractBlockFromResponse(response, action.blockData.block_type, action.blockData.order);
      if (!recreatedBlock) throw new Error('Failed to recreate block');
      
      // Normalize and add to state
      const normalizedBlock = normalizeBlock(recreatedBlock, action.blockData.block_type, action.blockData.order);
      sceneState.blocks.splice(action.position, 0, normalizedBlock);
      
      // Render and insert into DOM
      const container = document.getElementById('scene-content');
      const blockEl = renderBlockElement(normalizedBlock);
      
      if (action.position >= container.children.length) {
        container.appendChild(blockEl);
      } else {
        container.insertBefore(blockEl, container.children[action.position]);
      }
      
      // Restore content if it was modified
      if (action.blockData.content) {
        const blockType = blockEl.getAttribute('data-block-type');
        if (blockType === 'milestone') {
          const [subject, object] = action.blockData.content.split(' ');
          blockEl.querySelector('input[placeholder*="Subject"]').value = subject || '';
          blockEl.querySelector('input[placeholder*="Object"]').value = object || '';
        } else {
          const textarea = blockEl.querySelector('textarea');
          if (textarea) textarea.value = action.blockData.content;
        }
        
        // Save the restored content
        await StoryEngine.prototype.saveBlock.call(window.storyEngine, normalizedBlock.id, blockEl);
      }
    },
    
    // Undo block creation by deleting it
    async undoBlockCreate(action) {
      // Find and remove block from state
      const idx = sceneState.blocks.findIndex(b => b.id === action.blockId);
      if (idx >= 0) {
        sceneState.blocks.splice(idx, 1);
        renumberOrders();
      }
      
      // Remove from DOM
      const blockEl = document.querySelector(`details[data-block-id="${action.blockId}"]`);
      if (blockEl) {
        blockEl.remove();
      }
      
      // Call API to delete from server
      try {
        const response = await fetch(`/api/v1/content/blocks/${action.blockId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Delete failed: ${response.status}`);
        }
        
        const result = await response.json();
        if (!result.success) {
          throw new Error(result.error || 'Delete request failed');
        }
      } catch (error) {
        console.warn('[T5] Undo delete failed, but block removed from UI:', error);
        // Don't throw - the UI is already updated
      }
    },
    
    // Update undo button state
    updateUndoButton() {
      const undoButton = document.getElementById('undo-last-block');
      if (undoButton) {
        undoButton.disabled = this.stack.length === 0;
        undoButton.title = this.stack.length > 0 ? 
          `Undo ${this.stack[this.stack.length - 1].type} (${this.stack.length} actions available)` : 
          'Nothing to undo';
      }
    },
    
    // Clear the entire undo stack
    clear() {
      this.stack = [];
      this.updateUndoButton();
      console.debug('[T5] Undo stack cleared');
    }
  };

  // Utility: escape (reuse existing if available)
  function esc(str){ return (str??'').replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])); }

  // T9: Create individual dialogue line element
  function createDialogueLineElement(line, index, entityOptions) {
    const lineDiv = document.createElement('div');
    lineDiv.className = 'dialogue-line';
    lineDiv.innerHTML = `
      <div class="dialogue-line-controls">
        <select class="dialogue-speaker" data-field="speaker_id">
          <option value="">Select speaker...</option>
          ${entityOptions}
        </select>
        <button type="button" class="remove-dialogue-line" title="Remove line">✕</button>
      </div>
      <textarea class="dialogue-content" placeholder="Enter dialogue line..." rows="2">${esc(line.content)}</textarea>
    `;
    
    // Set selected speaker
    const speakerSelect = lineDiv.querySelector('.dialogue-speaker');
    if (line.speaker_id && speakerSelect) {
      speakerSelect.value = line.speaker_id;
    }
    
    return lineDiv;
  }

  // --- Step 3: Pure Block Renderer (DOM) -------------------------------------------------
  function renderBlockElement(block){
    const blockId = block.id || crypto.randomUUID();
    const type = block.block_type || 'prose';
    const details = document.createElement('details');
    details.open = true;
    details.dataset.blockId = blockId;
    details.dataset.blockType = type;
  details.className = 'scene-block-item';
  if (typeof block.order === 'number') details.dataset.order = String(block.order);

    const summary = document.createElement('summary');
    const hgroup = document.createElement('hgroup');
    const h4 = document.createElement('h4');
    const mark = document.createElement('mark');
    mark.textContent = type;
    h4.appendChild(mark);
    const p = document.createElement('p');
    p.className = 'block-preview';
    p.textContent = blockPreview(block);
    hgroup.appendChild(h4);
    hgroup.appendChild(p);

    const controls = document.createElement('div');
    controls.setAttribute('role','group');
    controls.innerHTML = `
      <button title="Move up" class="secondary outline" data-action="up">↑</button>
      <button title="Move down" class="secondary outline" data-action="down">↓</button>
      <button title="Delete" class="secondary outline" data-action="delete">✕</button>`;

    summary.appendChild(hgroup);
    summary.appendChild(controls);
    details.appendChild(summary);

    const bodyWrapper = document.createElement('div');
    bodyWrapper.appendChild(buildBlockContent(type, block));
    details.appendChild(bodyWrapper);

    // Control handlers (reorder & delete)
    controls.addEventListener('click', (e)=>{
      e.stopPropagation();
      const action = e.target?.dataset.action;
      if (!action) return;
      console.debug('[scene-editor] control action', {action, blockId, order:block.order});
      if (action === 'delete') {
        deleteBlock(blockId);
      } else if (action === 'up') {
        moveBlock(blockId, -1);
      } else if (action === 'down') {
        moveBlock(blockId, +1);
      }
    });

    return details;
  }

  function blockPreview(block){
    const type = block.block_type || 'prose';
    let content = block.content || '';
    
    if (type === 'milestone' && content.length === 0){
      // T8: Handle both legacy (text) and new (structured) milestone data
      let subjectName = block.subject || '';
      let verb = block.verb || '—';
      let objectName = block.object || '';
      
      // If we have structured data, try to resolve entity names
      if (block.subject_id && sceneState.entities) {
        const subjectEntity = sceneState.entities.find(e => e.id === block.subject_id);
        if (subjectEntity) subjectName = subjectEntity.name;
      }
      if (block.object_id && sceneState.entities) {
        const objectEntity = sceneState.entities.find(e => e.id === block.object_id);
        if (objectEntity) objectName = objectEntity.name;
      }
      
      content = [subjectName, verb, objectName].filter(Boolean).join(' ');
    }
    
    if (type === 'dialogue' && content.length === 0 && block.lines && Array.isArray(block.lines) && block.lines.length > 0) {
      // T9: Handle structured dialogue data
      const firstLine = block.lines[0];
      let speakerName = '';
      
      // Try to resolve speaker name from entity
      if (firstLine.speaker_id && sceneState.entities) {
        const speaker = sceneState.entities.find(e => e.id === firstLine.speaker_id);
        if (speaker) speakerName = speaker.name;
      }
      
      const lineContent = firstLine.content || '';
      content = speakerName ? `${speakerName}: ${lineContent}` : lineContent;
      
      // Add indicator if there are multiple lines
      if (block.lines.length > 1) {
        content += ` (+${block.lines.length - 1} more)`;
      }
    }
    
    return content.length > 50 ? content.slice(0,50)+'…' : content || '(empty)';
  }

  function buildBlockContent(type, block){
    if (type === 'dialogue') {
      const fieldset = document.createElement('fieldset');
      
      // T9: Parse existing dialogue data - support both legacy text and structured lines
      let dialogueLines = [];
      
      if (block.lines && Array.isArray(block.lines)) {
        // Structured dialogue data
        dialogueLines = block.lines;
      } else if (block.content && block.content.trim()) {
        // Legacy text content - convert to single line for backward compatibility
        dialogueLines = [{ speaker_id: '', content: block.content.trim() }];
      } else {
        // Empty dialogue - start with one empty line
        dialogueLines = [{ speaker_id: '', content: '' }];
      }
      
      // Build entity options for speaker dropdowns
      const entityOptions = sceneState.entities.map(e => 
        `<option value="${e.id}">${esc(e.name)} (${esc(e.entity_type)})</option>`
      ).join('');
      
      // Create structured dialogue interface
      fieldset.innerHTML = `
        <legend>Dialogue</legend>
        <div class="dialogue-structured">
          <div class="dialogue-lines" data-lines-container></div>
          <div class="dialogue-controls">
            <button type="button" class="add-dialogue-line" data-action="add-line">+ Add Line</button>
          </div>
        </div>`;
      
      const linesContainer = fieldset.querySelector('[data-lines-container]');
      
      // Render existing dialogue lines
      dialogueLines.forEach((line, index) => {
        const lineEl = createDialogueLineElement(line, index, entityOptions);
        linesContainer.appendChild(lineEl);
      });
      
      // Add event listeners
      fieldset.addEventListener('click', (e) => {
        if (e.target.matches('.add-dialogue-line')) {
          e.preventDefault();
          const newLine = { speaker_id: '', content: '' };
          const lineEl = createDialogueLineElement(newLine, dialogueLines.length, entityOptions);
          linesContainer.appendChild(lineEl);
          // Focus the new content field
          lineEl.querySelector('.dialogue-content').focus();
        } else if (e.target.matches('.remove-dialogue-line')) {
          e.preventDefault();
          const lineEl = e.target.closest('.dialogue-line');
          if (lineEl && linesContainer.children.length > 1) {
            lineEl.remove();
          }
        }
      });
      
      return fieldset;
    }
    if (type === 'milestone') {
      const fieldset = document.createElement('fieldset');
      
      // Build entity options for dropdowns
      const entityOptions = sceneState.entities.map(e => 
        `<option value="${e.id}">${esc(e.name)} (${esc(e.entity_type)})</option>`
      ).join('');
      
      // Get current values - handle both legacy (text) and new (ID) formats
      const subjectId = block.subject_id || '';
      const subjectName = block.subject || '';
      const objectId = block.object_id || '';
      const objectName = block.object || '';
      const verb = block.verb || 'discovers';
      
      fieldset.innerHTML = `
        <legend>Milestone</legend>
        <div class="milestone-structured">
          <div class="milestone-field">
            <label>Subject (Who/What)
              <select class="milestone-subject" data-field="subject_id">
                <option value="">Select entity...</option>
                ${entityOptions}
              </select>
            </label>
            ${subjectName && !subjectId ? `<small>Legacy: "${esc(subjectName)}"</small>` : ''}
          </div>
          <div class="milestone-field">
            <label>Action (Verb)
              <input type="text" class="milestone-verb" data-field="verb" 
                     value="${esc(verb)}" placeholder="discovers, learns, defeats...">
            </label>
          </div>
          <div class="milestone-field">
            <label>Object (What/Outcome)
              <select class="milestone-object" data-field="object_id">
                <option value="">Select entity (optional)...</option>
                ${entityOptions}
              </select>
            </label>
            ${objectName && !objectId ? `<small>Legacy: "${esc(objectName)}"</small>` : ''}
          </div>
        </div>`;
      
      // Set selected values
      const subjectSelect = fieldset.querySelector('.milestone-subject');
      const objectSelect = fieldset.querySelector('.milestone-object');
      if (subjectId && subjectSelect) subjectSelect.value = subjectId;
      if (objectId && objectSelect) objectSelect.value = objectId;
      
      return fieldset;
    }
    // prose default
    const div = document.createElement('div');
    div.className = 'prose-content';
    div.innerHTML = `<textarea placeholder="Write your prose here...">${esc(block.content||'')}</textarea>`;
    return div;
  }

  // Override core renderScene to use stateful DOM rendering
  StoryEngine.prototype.renderScene = function(scene, blocks, entities){
    this.currentSceneId = scene.id;
    sceneState.current = scene;
    sceneState.blocks = blocks.slice();
    sceneState.entities = entities.slice();
    normalizeOrders();
    // Header
    this.updateElement('scene-title', esc(scene.title || 'Untitled Scene'));
    this.updateElement('scene-timestamp', scene.timestamp || '1');
    this.updateElement('scene-id', scene.id);
    // Entities
    if (!entities || entities.length === 0) {
      this.updateElement('linked-entities', '<p><em>No linked entities</em></p>');
    } else {
      const html = entities.map(e=>`<kbd data-tooltip="${esc(e.entity_type)}" data-id="${e.id}">${esc(e.name)}</kbd>`).join(' ');
      this.updateElement('linked-entities', html);
    }
    // Blocks container
    const container = document.getElementById('scene-content');
    if (container){
      container.innerHTML = '';
      sceneState.blocks.forEach(b=>container.appendChild(renderBlockElement(b)));
    }
    // Navigation
    this.updateInlineNav?.();
    bus.emit('scene:loaded', { scene, blocks: sceneState.blocks });
  };

  // Update existing block preview after autosave
  function updateBlockPreview(blockId, newContent){
    const details = document.querySelector(`details[data-block-id="${blockId}"]`);
    if (!details) return;
    const previewEl = details.querySelector('.block-preview');
    if (previewEl) previewEl.textContent = newContent.length>50? newContent.slice(0,50)+'…': (newContent||'(empty)');
  }

  // Patch saveBlock to update state + preview + track undo (T5)
  const originalSaveBlock = StoryEngine.prototype.saveBlock;
  StoryEngine.prototype.saveBlock = async function(blockId, detailsEl){
    // T5: Capture previous content for undo
    const blockIdx = sceneState.blocks.findIndex(b=>b.id===blockId);
    let previousContent = '';
    
    if (blockIdx >= 0) {
      const blockType = detailsEl.getAttribute('data-block-type');
      if (blockType === 'milestone') {
        // T8: Get structured milestone content for comparison
        const subjectSelect = detailsEl.querySelector('.milestone-subject');
        const verbInput = detailsEl.querySelector('.milestone-verb');
        const objectSelect = detailsEl.querySelector('.milestone-object');
        
        const subjectName = subjectSelect?.selectedOptions[0]?.textContent || '';
        const verb = verbInput?.value.trim() || '';
        const objectName = objectSelect?.selectedOptions[0]?.textContent || '';
        previousContent = objectName ? `${subjectName} ${verb} ${objectName}` : `${subjectName} ${verb}`;
      } else if (blockType === 'dialogue') {
        // T9: Get structured dialogue content for comparison
        const dialogueLines = detailsEl.querySelectorAll('.dialogue-line');
        const lineTexts = Array.from(dialogueLines).map(line => {
          const speakerSelect = line.querySelector('.dialogue-speaker');
          const contentTextarea = line.querySelector('.dialogue-content');
          const speakerName = speakerSelect?.selectedOptions[0]?.textContent || '';
          const content = contentTextarea?.value || '';
          return speakerName ? `${speakerName}: ${content}` : content;
        }).filter(Boolean);
        previousContent = lineTexts.join('\n');
      } else {
        previousContent = detailsEl.querySelector('textarea')?.value || '';
      }
      
      // Store current content as previous content before the save
      const existingContent = sceneState.blocks[blockIdx].content || '';
      
      // Only track undo if content actually changed
      if (existingContent !== previousContent) {
        undoStack.push({
          type: 'block-content',
          blockId: blockId,
          previousContent: existingContent,
          timestamp: Date.now()
        });
      }
    }
    
    await originalSaveBlock.call(this, blockId, detailsEl);
    try {
      if (blockIdx>=0){
        const blockType = detailsEl.getAttribute('data-block-type');
        let content='';
        if (blockType==='milestone') {
          // T8: Update local state with structured milestone data
          const subjectSelect = detailsEl.querySelector('.milestone-subject');
          const verbInput = detailsEl.querySelector('.milestone-verb');
          const objectSelect = detailsEl.querySelector('.milestone-object');
          
          // Update structured fields in local state
          if (subjectSelect?.value) {
            sceneState.blocks[blockIdx].subject_id = subjectSelect.value;
          }
          if (verbInput?.value.trim()) {
            sceneState.blocks[blockIdx].verb = verbInput.value.trim();
          }
          if (objectSelect?.value) {
            sceneState.blocks[blockIdx].object_id = objectSelect.value;
          }
          
          // Update content for display
          const subjectName = subjectSelect?.selectedOptions[0]?.textContent || 'Someone';
          const verb = verbInput?.value.trim() || 'does something';
          const objectName = objectSelect?.selectedOptions[0]?.textContent || '';
          content = objectName ? `${subjectName} ${verb} ${objectName}` : `${subjectName} ${verb}`;
        } else if (blockType === 'dialogue') {
          // T9: Update local state with structured dialogue data
          const dialogueLines = detailsEl.querySelectorAll('.dialogue-line');
          const lines = Array.from(dialogueLines).map(line => {
            const speakerSelect = line.querySelector('.dialogue-speaker');
            const contentTextarea = line.querySelector('.dialogue-content');
            return {
              speaker_id: speakerSelect?.value || '',
              content: contentTextarea?.value || ''
            };
          }).filter(line => line.content.trim()); // Only keep non-empty lines
          
          // Update structured dialogue data in local state
          sceneState.blocks[blockIdx].lines = lines;
          
          // Generate readable content for display
          content = lines.map(line => {
            const speakerName = line.speaker_id ? 
              (sceneState.entities.find(e => e.id === line.speaker_id)?.name || 'Unknown') : 
              '';
            return speakerName ? `${speakerName}: ${line.content}` : line.content;
          }).join('\n');
        } else {
          content = detailsEl.querySelector('textarea')?.value || '';
        }
        sceneState.blocks[blockIdx].content = content;
        updateBlockPreview(blockId, content);
        bus.emit('block:saved', { id:blockId, content });
      }
    } catch(e){ console.warn('Post-save update failed', e); }
  };

  // Patch addBlock to append without full reload
  const originalAddBlock = StoryEngine.prototype.addBlock;
  StoryEngine.prototype.addBlock = async function(type){
    const container = document.getElementById('scene-content');
    if (!container) return;
    let newBlock;
    try {
      newBlock = await originalAddBlock.call(this, type);
    } catch(e){
      console.error('addBlock failed', e);
      updateGlobalStatus('Block creation failed', 'error');
      return;
    }
    if (!newBlock) {
      updateGlobalStatus('No block returned from API', 'warn');
      return;
    }
    
    // T3: Normalize and validate block shape
    newBlock = normalizeBlock(newBlock, type, sceneState.blocks.length);
    const validation = validateBlock(newBlock);
    
    if (!validation.valid) {
      console.error('Block validation failed:', validation.errors, newBlock);
      updateGlobalStatus(`Block validation failed: ${validation.errors.join(', ')}`, 'error');
      return;
    }
    
    // Push into in-memory state
    sceneState.blocks.push(newBlock);
    renumberOrders();
    
    // T5: Track block creation for undo
    undoStack.push({
      type: 'block-create',
      blockId: newBlock.id,
      timestamp: Date.now()
    });
    
    // Render & append
    const el = renderBlockElement(newBlock);
    container.appendChild(el);
    // Focus first editable field for usability
    const focusable = el.querySelector('textarea, input[type="text"]');
    focusable?.focus();
    updateGlobalStatus(`Added ${type} block`, 'info');
    bus.emit('block:added', { block: newBlock });
  };

  // Expose bus subscribe helpers on prototype
  StoryEngine.prototype.on = function(evt, fn){ return bus.on(evt, fn); };
  StoryEngine.prototype.emit = function(evt, data){ return bus.emit(evt, data); };

  // ---------------------------------------------------------------
  // Helpers added for incremental path & status feedback (T1)
  // ---------------------------------------------------------------
  
  // T3: Validate block object has minimum required fields
  function validateBlock(block) {
    if (!block || typeof block !== 'object') {
      return { valid: false, errors: ['Block is not an object'] };
    }
    
    const errors = [];
    
    // Required fields
    if (!block.id) {
      errors.push('Missing required field: id');
    }
    if (!block.block_type) {
      errors.push('Missing required field: block_type');
    }
    if (block.order === undefined || block.order === null) {
      errors.push('Missing required field: order');
    }
    
    // Type validation
    if (block.block_type && !['prose', 'dialogue', 'milestone'].includes(block.block_type)) {
      errors.push(`Invalid block_type: ${block.block_type}`);
    }
    
    // Order should be a number
    if (block.order !== undefined && typeof block.order !== 'number') {
      errors.push(`Invalid order type: expected number, got ${typeof block.order}`);
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  // Robust block normalization for T3 - handles all possible API response variations
  function normalizeBlock(raw, fallbackType, order){
    if (!raw || typeof raw !== 'object') {
      console.warn('normalizeBlock: Invalid raw block, creating fallback', raw);
      raw = {};
    }
    
    // Primary fields with multiple fallback keys
    const id = raw.id || raw.block_id || raw.uuid || crypto.randomUUID();
    const block_type = raw.block_type || raw.type || fallbackType || 'prose';
    const content = raw.content || raw.text || '';
    const scene_id = raw.scene_id || null;
    
    // Order with smart fallback
    const normalizedOrder = raw.order !== undefined ? raw.order : order;
    
    // Optional structured fields (milestone/dialogue specific)
    const subject_id = raw.subject_id || null;
    const verb = raw.verb || '';
    const object_id = raw.object_id || null;
    const weight = raw.weight !== undefined ? raw.weight : null;
    const lines = raw.lines || null; // For dialogue
    const summary = raw.summary || '';
    
    // Metadata and timestamps
    const created_at = raw.created_at || raw.createdAt || new Date().toISOString();
    const updated_at = raw.updated_at || raw.updatedAt || created_at;
    const metadata = raw.metadata || raw.meta || {};
    
    // Return canonical block object with all fields
    const normalized = {
      id,
      scene_id,
      block_type,
      order: normalizedOrder,
      content,
      summary,
      lines,
      subject_id,
      verb,
      object_id,
      weight,
      metadata,
      created_at,
      updated_at
    };
    
    console.debug('[T3] Block normalized:', { raw, normalized });
    return normalized;
  }

  function updateGlobalStatus(message, level='info'){
    const el = document.getElementById('scene-global-status');
    if (!el) return;
    
    const ts = new Date().toLocaleTimeString();
    const iconEl = el.querySelector('.status-icon');
    const messageEl = el.querySelector('.status-message');
    
    // Set status level and icon
    el.dataset.level = level;
    
    const icons = {
      info: 'ℹ️',
      success: '✅',
      warn: '⚠️',
      error: '❌',
      loading: '⟳'
    };
    
    if (iconEl) iconEl.textContent = icons[level] || icons.info;
    if (messageEl) messageEl.textContent = `[${ts}] ${message}`;
  }

  async function moveBlock(blockId, delta){
    const arr = sceneState.blocks;
    const idx = arr.findIndex(b=>b.id===blockId);
    if (idx < 0) return;
    const newIdx = idx + delta;
    if (newIdx < 0 || newIdx >= arr.length) return; // boundary
    
    // T5: Capture previous order for undo
    const previousOrder = arr.map(b => b.id);
    
    // Reinsert item at newIdx preserving relative order
    const [item] = arr.splice(idx,1);
    arr.splice(newIdx,0,item);
    renumberOrders();
    console.debug('[scene-editor] moveBlock after', { after: sceneState.blocks.map(b => b.id) });
    rerenderBlocks();
    updateGlobalStatus(`Reordered block ${blockId.slice(0, 8)}`);
    bus.emit('block:reordered', { id: blockId, to: newIdx });
    
    // T5: Track reorder for undo (after successful visual update)
    undoStack.push({
      type: 'block-reorder',
      blockId: blockId,
      previousOrder: previousOrder,
      timestamp: Date.now()
    });
    
    persistReorder();
  }

  let _reorderTimer;
  function persistReorder(){
    clearTimeout(_reorderTimer);
    _reorderTimer = setTimeout(async ()=>{
      try {
        const sceneId = sceneState.current?.id;
        if (!sceneId) return;
        const block_order = Object.fromEntries(sceneState.blocks.map(b=>[b.id, b.order]));
        const resp = await fetch('/api/v1/content/blocks/reorder', {
          method: 'POST',
          headers: { 'Content-Type':'application/json' },
          body: JSON.stringify({ scene_id: sceneId, block_order })
        });
        if (!resp.ok) throw new Error('Reorder failed');
        updateGlobalStatus('Block order saved', 'success');
      } catch(e){
        console.error('Persist reorder error', e);
        updateGlobalStatus('Reorder save failed', 'error');
      }
    }, 300); // small debounce to allow rapid multi-moves
  }

  function renumberOrders(){
    sceneState.blocks.forEach((b,i)=> b.order = i);
  }

  function normalizeOrders(){
    // Sort by existing order then reindex sequentially
    sceneState.blocks.sort((a,b)=> (a.order??0) - (b.order??0));
    renumberOrders();
  }

  function rerenderBlocks(){
    const container = document.getElementById('scene-content');
    if (!container) return;
    container.innerHTML = '';
  // Ensure order display matches internal order
  sceneState.blocks.forEach((b,i)=> { b.order = i; const el = renderBlockElement(b); el.dataset.order = String(i); container.appendChild(el);});
  }

  async function deleteBlock(blockId){
    console.debug('[scene-editor] deleteBlock start', {blockId});
    
    // Find block and preserve state for rollback
    const idx = sceneState.blocks.findIndex(b => b.id === blockId);
    if (idx < 0) {
      console.warn('[scene-editor] deleteBlock: block not found in state');
      return;
    }
    
    const blockToDelete = sceneState.blocks[idx];
    const blockElement = document.querySelector(`details[data-block-id="${blockId}"]`);
    
    // Capture current content for undo tracking
    let currentContent = blockToDelete.content || '';
    if (blockElement) {
      const blockType = blockElement.getAttribute('data-block-type');
      if (blockType === 'milestone') {
        const inputs = blockElement.querySelectorAll('input[type="text"]');
        currentContent = Array.from(inputs).map(i=>i.value.trim()).filter(Boolean).join(' ');
      } else {
        const textarea = blockElement.querySelector('textarea');
        if (textarea) currentContent = textarea.value;
      }
    }
    
    // Optimistic removal: update state and DOM immediately
    sceneState.blocks.splice(idx, 1);
    renumberOrders(); // Fix order sequence after removal
    if (blockElement) blockElement.remove();
    
    updateGlobalStatus(`Deleting block ${blockId.slice(0,8)}...`, 'loading');
    bus.emit('block:deleted', { id: blockId });
    
    try {
      // Call delete API
      const response = await fetch(`/api/v1/content/blocks/${blockId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Delete failed: ${response.status}`);
      }
      
      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Delete request failed');
      }
      
      // T5: Track successful deletion for undo
      undoStack.push({
        type: 'block-delete',
        blockId: blockId,
        blockData: { ...blockToDelete, content: currentContent },
        position: idx,
        timestamp: Date.now()
      });
      
      updateGlobalStatus(`Block ${blockId.slice(0,8)} deleted`, 'success');
      console.debug('[scene-editor] deleteBlock success');
      
    } catch (error) {
      console.error('[scene-editor] deleteBlock error:', error);
      
      // Rollback: restore block to state and DOM
      sceneState.blocks.splice(idx, 0, blockToDelete);
      renumberOrders();
      rerenderBlocks(); // Full rerender to restore proper position
      
      updateGlobalStatus(`Delete failed: ${error.message}`, 'error');
      bus.emit('block:delete-failed', { id: blockId, error: error.message });
    }
  }

  // Listen to key bus events for baseline status updates
  bus.on('scene:loaded', ({scene})=> updateGlobalStatus(`Loaded scene "${(scene.title||'Untitled').slice(0,40)}"`, 'success'));
  bus.on('block:saved', ({id})=> updateGlobalStatus(`Block ${id.slice(0,8)} saved`, 'success'));
  bus.on('block:deleted', ({id})=> updateGlobalStatus(`Block ${id.slice(0,8)} deleted`, 'success'));

  // T5: Initialize undo button functionality
  function initializeUndoButton() {
    const undoButton = document.getElementById('undo-last-block');
    if (undoButton) {
      // Remove any existing event listeners
      undoButton.removeEventListener('click', handleUndoClick);
      
      // Add fresh event listener
      undoButton.addEventListener('click', handleUndoClick);
      
      // Initialize button state
      undoStack.updateUndoButton();
      console.debug('[T5] Undo button initialized');
    } else {
      console.warn('[T5] Undo button not found');
    }
  }
  
  async function handleUndoClick() {
    console.debug('[T5] Undo button clicked');
    await undoStack.pop();
  }
  
  // Initialize immediately if DOM is ready, or wait for it
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUndoButton);
  } else {
    initializeUndoButton();
  }
  
  // T5: Update undo button state when scene loads
  bus.on('scene:loaded', () => {
    undoStack.clear(); // Clear undo stack when loading new scene
    setTimeout(initializeUndoButton, 100); // Re-initialize after scene loads
  });

  // --- T7: Dirty Navigation Guard -------------------------------------------------
  
  // Check if there are any unsaved changes
  function hasUnsavedChanges() {
    const engine = window.storyEngine;
    if (!engine) return false;
    
    // Check scene-level dirty state
    if (engine._sceneDirty) {
      console.debug('[T7] Scene has unsaved changes');
      return true;
    }
    
    // Check block-level dirty state
    if (engine._dirtyBlocks && engine._dirtyBlocks.size > 0) {
      console.debug('[T7] Blocks have unsaved changes:', Array.from(engine._dirtyBlocks));
      return true;
    }
    
    // Check for pending save operations
    if (engine._sceneSaveTimer) {
      console.debug('[T7] Scene save pending');
      return true;
    }
    
    if (engine._debouncers && Object.keys(engine._debouncers).length > 0) {
      console.debug('[T7] Block saves pending:', Object.keys(engine._debouncers));
      return true;
    }
    
    return false;
  }
  
  // Generate user-friendly message about what will be lost
  function getUnsavedChangesMessage() {
    const engine = window.storyEngine;
    const changes = [];
    
    if (engine?._sceneDirty) {
      changes.push('scene title/metadata');
    }
    
    if (engine?._dirtyBlocks?.size > 0) {
      changes.push(`${engine._dirtyBlocks.size} block(s) content`);
    }
    
    if (engine?._sceneSaveTimer) {
      changes.push('scene save in progress');
    }
    
    if (engine?._debouncers && Object.keys(engine._debouncers).length > 0) {
      changes.push('block saves in progress');
    }
    
    if (changes.length === 0) return null;
    
    return `You have unsaved changes: ${changes.join(', ')}. Are you sure you want to leave?`;
  }
  
  // Browser beforeunload handler
  function handleBeforeUnload(event) {
    if (hasUnsavedChanges()) {
      const message = 'You have unsaved changes in the scene editor. Are you sure you want to leave?';
      event.preventDefault();
      event.returnValue = message; // For older browsers
      return message;
    }
  }
  
  // Internal navigation guard for SPA navigation
  function guardNavigation(targetPage, callback) {
    // Only guard when leaving the scene editor
    if (window.pageLoader?.currentPage !== 'scene-editor') {
      callback(true);
      return;
    }
    
    if (!hasUnsavedChanges()) {
      callback(true);
      return;
    }
    
    const message = getUnsavedChangesMessage();
    const proceed = confirm(message);
    
    if (proceed) {
      // Clear dirty state since user confirmed they want to lose changes
      clearDirtyState();
      console.log('[T7] Navigation confirmed, clearing dirty state');
    } else {
      console.log('[T7] Navigation cancelled by user');
    }
    
    callback(proceed);
  }
  
  // Clear all dirty state (when user confirms navigation or saves complete)
  function clearDirtyState() {
    const engine = window.storyEngine;
    if (!engine) return;
    
    engine._sceneDirty = false;
    if (engine._dirtyBlocks) engine._dirtyBlocks.clear();
    
    // Clear any pending timers
    if (engine._sceneSaveTimer) {
      clearTimeout(engine._sceneSaveTimer);
      engine._sceneSaveTimer = null;
    }
    
    if (engine._debouncers) {
      Object.values(engine._debouncers).forEach(timer => clearTimeout(timer));
      engine._debouncers = {};
    }
  }
  
  // Initialize navigation guards
  function initializeNavigationGuards() {
    // Browser navigation guard
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Internal navigation guard - hook into page loader if available
    if (window.pageLoader && typeof window.pageLoader.setNavigationGuard === 'function') {
      window.pageLoader.setNavigationGuard(guardNavigation);
      console.debug('[T7] Navigation guard registered with page loader');
    } else {
      // Fallback: try to register later when page loader is ready
      setTimeout(() => {
        if (window.pageLoader && typeof window.pageLoader.setNavigationGuard === 'function') {
          window.pageLoader.setNavigationGuard(guardNavigation);
          console.debug('[T7] Navigation guard registered with page loader (delayed)');
        } else {
          console.warn('[T7] Page loader navigation guard not available');
        }
      }, 1000);
    }
    
    console.debug('[T7] Navigation guards initialized');
  }
  
  // Clear dirty state when saves complete successfully
  bus.on('block:saved', () => {
    const engine = window.storyEngine;
    if (engine?._dirtyBlocks?.size === 0 && !engine._sceneDirty) {
      console.debug('[T7] All changes saved, clearing dirty timers');
    }
  });
  
  // Initialize navigation guards when the module loads
  initializeNavigationGuards();
  
  // Expose for debugging
  window.sceneNavigationGuard = {
    hasUnsavedChanges,
    getUnsavedChangesMessage,
    clearDirtyState,
    guardNavigation
  };

})();
