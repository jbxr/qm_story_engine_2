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

  // Utility: escape (reuse existing if available)
  function esc(str){ return (str??'').replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])); }

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
        // Soft delete for now
        details.remove();
        const idx = sceneState.blocks.findIndex(b=>b.id===blockId);
        if (idx>=0) { sceneState.blocks.splice(idx,1); }
        bus.emit('block:deleted', { id: blockId });
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
      const subj = block.subject || ''; const verb = block.verb || '—'; const obj = block.object || '';
      content = [subj, verb, obj].filter(Boolean).join(' ');
    }
    return content.length > 50 ? content.slice(0,50)+'…' : content || '(empty)';
  }

  function buildBlockContent(type, block){
    if (type === 'dialogue') {
      const fieldset = document.createElement('fieldset');
      fieldset.innerHTML = `
        <legend>Dialogue</legend>
        <textarea placeholder="Write dialogue here...">${esc(block.content||'')}</textarea>`;
      return fieldset;
    }
    if (type === 'milestone') {
      const fieldset = document.createElement('fieldset');
      fieldset.innerHTML = `
        <legend>Milestone</legend>
        <div class="grid">
          <label>Subject<input type="text" value="${esc(block.subject||'')}" placeholder="Who/What"></label>
          <div style="display:flex;align-items:end;justify-content:center;"><mark>${esc(block.verb||'discovers')}</mark></div>
          <label>Object<input type="text" value="${esc(block.object||'')}" placeholder="Outcome"></label>
        </div>`;
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

  // Patch saveBlock to update state + preview (if previously defined)
  const originalSaveBlock = StoryEngine.prototype.saveBlock;
  StoryEngine.prototype.saveBlock = async function(blockId, detailsEl){
    await originalSaveBlock.call(this, blockId, detailsEl);
    try {
      const blockIdx = sceneState.blocks.findIndex(b=>b.id===blockId);
      if (blockIdx>=0){
        const blockType = detailsEl.getAttribute('data-block-type');
        let content='';
        if (blockType==='milestone') {
          const inputs = detailsEl.querySelectorAll('input[type="text"]');
            content = Array.from(inputs).map(i=>i.value.trim()).filter(Boolean).join(' ');
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
    // Normalize block shape (T3 groundwork)
  newBlock = normalizeBlock(newBlock, type, sceneState.blocks.length);
    // Push into in-memory state
    sceneState.blocks.push(newBlock);
  renumberOrders();
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
  function normalizeBlock(raw, fallbackType, order){
    if (!raw || typeof raw !== 'object') raw = {};
    // Accept various possible keys for id / type / content
    const id = raw.id || raw.block_id || raw.uuid || crypto.randomUUID();
    const block_type = raw.block_type || raw.type || fallbackType || 'prose';
    const content = raw.content || '';
    return { id, block_type, content, order: raw.order ?? order };
  }

  function updateGlobalStatus(message, level='info'){
    const el = document.getElementById('scene-global-status');
    if (!el) return;
    const ts = new Date().toLocaleTimeString();
    el.textContent = `[${ts}] ${message}`;
    el.dataset.level = level;
  }

  async function moveBlock(blockId, delta){
    const arr = sceneState.blocks;
    const idx = arr.findIndex(b=>b.id===blockId);
    if (idx < 0) return;
    const newIdx = idx + delta;
    if (newIdx < 0 || newIdx >= arr.length) return; // boundary
    // Reinsert item at newIdx preserving relative order
    const [item] = arr.splice(idx,1);
    arr.splice(newIdx,0,item);
    renumberOrders();
    console.debug('[scene-editor] moveBlock after', { after: sceneState.blocks.map(b => b.id) });
    rerenderBlocks();
    updateGlobalStatus(`Reordered block ${blockId.slice(0, 8)}`);
    bus.emit('block:reordered', { id: blockId, to: newIdx });
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
        updateGlobalStatus('Block order saved');
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

  // Listen to key bus events for baseline status updates
  bus.on('scene:loaded', ({scene})=> updateGlobalStatus(`Loaded scene "${(scene.title||'Untitled').slice(0,40)}"`));
  bus.on('block:saved', ({id})=> updateGlobalStatus(`Block ${id.slice(0,8)} saved`));
  bus.on('block:deleted', ({id})=> updateGlobalStatus(`Block ${id.slice(0,8)} deleted`));

})();
