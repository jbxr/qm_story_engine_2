// Scene Editor Module - extracted from app.js to keep core engine lean
// Attaches editor-specific methods to StoryEngine prototype

(function(){
  if (typeof StoryEngine === 'undefined') {
    console.error('Scene Editor module loaded before StoryEngine');
    return;
  }

  // Load a scene into the editor page after it is inserted into DOM
  StoryEngine.prototype.loadSceneIntoEditor = async function(sceneId) {
    try {
      console.log('📝 Loading scene into editor:', sceneId);
      if (!this.scenes || this.scenes.length === 0) {
        await this.loadScenesData();
      }
      const { data: scene, error } = await this.supabase
        .from('scenes')
        .select('*')
        .eq('id', sceneId)
        .single();
      if (error) throw error;
      let blocks = [];
      try { const r = await this.api.getSceneBlocks(sceneId); blocks = r.data?.blocks || []; } catch(e){ console.warn('Blocks load failed', e);}
      let entities = [];
      try { const er = await this.api.getSceneEntities(sceneId); entities = er.data?.entities || []; } catch(e){ console.warn('Entities load failed', e);}
      this.renderScene(scene, blocks, entities);
      this.populateSceneMetadata(sceneId, scene);
      this.attachSceneEditorHandlers();
    } catch (err) {
      console.error('Failed to load scene into editor:', err);
      this.updateElement('scene-content', `<p class="error">Failed to load scene: ${this.escapeHtml(err.message)}</p>`);
    }
  };

  StoryEngine.prototype.populateSceneMetadata = function(sceneId, scene) {
    const locSelect = document.getElementById('scene-location');
    if (locSelect) {
      const uniqueLocations = Array.from(new Set(this.scenes.map(s => s.location_id).filter(Boolean)));
      locSelect.innerHTML = '<option value="">Select location...</option>' +
        uniqueLocations.map(loc => `<option value="${this.escapeHtml(loc)}">${this.escapeHtml(loc)}</option>`).join('');
      if (scene.location_id) locSelect.value = scene.location_id;
    }
    const prevSelect = document.getElementById('scene-previous');
    const nextSelect = document.getElementById('scene-next');
    if (prevSelect && nextSelect) {
      const index = this.scenes.findIndex(s => s.id === sceneId);
      const before = this.scenes.slice(0, index);
      const after = this.scenes.slice(index + 1);
      prevSelect.innerHTML = '<option value="">None</option>' + before.map(s => `<option value="${s.id}">${this.escapeHtml(s.title || 'Untitled')}</option>`).join('');
      nextSelect.innerHTML = '<option value="">None</option>' + after.map(s => `<option value="${s.id}">${this.escapeHtml(s.title || 'Untitled')}</option>`).join('');
      if (before.length) prevSelect.value = before[before.length - 1].id;
      if (after.length) nextSelect.value = after[0].id;
    }
  };

  StoryEngine.prototype.attachSceneEditorHandlers = function() {
    if (this._sceneEditorHandlersAttached) return;
    document.getElementById('run-continuity')?.addEventListener('click', () => this.runContinuityAnalysis());
    const wqForm = document.getElementById('world-query-form');
    const wqInput = document.getElementById('world-query-input');
    if (wqForm && wqInput) {
      wqForm.addEventListener('submit', e => { e.preventDefault(); const q = wqInput.value.trim(); if (!q) return; this.queryWorld(q); wqInput.value=''; });
    }
    document.getElementById('add-prose')?.addEventListener('click', () => this.addBlock('prose'));
    document.getElementById('add-dialogue')?.addEventListener('click', () => this.addBlock('dialogue'));
    document.getElementById('add-milestone')?.addEventListener('click', () => this.addBlock('milestone'));
    document.getElementById('save-scene-btn')?.addEventListener('click', () => this.saveSceneChanges());
    const titleEl = document.getElementById('scene-title');
    if (titleEl) titleEl.addEventListener('input', () => { this.markSceneDirty(); this.debounceSceneSave(); });
    document.getElementById('scene-location')?.addEventListener('change', () => { this.markSceneDirty(); this.saveSceneChanges(); });
    document.getElementById('scene-nav-list')?.addEventListener('click', e => { e.preventDefault(); window.pageLoader?.loadPage('scenes'); });
    document.getElementById('scene-nav-prev')?.addEventListener('click', e => { e.preventDefault(); this.navigateRelativeScene(-1); });
    document.getElementById('scene-nav-next')?.addEventListener('click', e => { e.preventDefault(); this.navigateRelativeScene(1); });
    document.getElementById('scene-content')?.addEventListener('input', (e) => {
      const t = e.target;
      if (t.tagName === 'TEXTAREA' || (t.tagName === 'INPUT' && t.type === 'text')) {
        const details = t.closest('details[data-block-id]');
        if (details) { const blockId = details.getAttribute('data-block-id'); this.markBlockDirty(blockId); this.debounceBlockSave(blockId, details); }
      }
    });
    this._debouncers = {};
    this._sceneEditorHandlersAttached = true;
  };

  StoryEngine.prototype.runContinuityAnalysis = function() {
    const container = document.querySelector('#continuity-analysis .continuity-body');
    if (!container) return;
    container.innerHTML = '<p><span aria-busy="true">Analyzing continuity...</span></p>';
    const sceneId = document.getElementById('scene-id')?.textContent || '';
    setTimeout(() => {
      container.innerHTML = `<p><strong>Summary:</strong> No inconsistencies detected.</p><p><small>Scene ${this.escapeHtml(sceneId)} passes baseline checks (placeholder).</small></p>`;
    }, 800);
  };

  StoryEngine.prototype.queryWorld = function(query) {
    const results = document.getElementById('world-query-results');
    if (!results) return;
    const ts = new Date().toLocaleTimeString();
    const placeholderAnswer = `Stub answer for "${this.escapeHtml(query)}" (integrate /api/search or knowledge soon).`;
    const item = document.createElement('div');
    item.className = 'query-item';
    item.innerHTML = `<p><strong>${ts}</strong> <mark>Q:</mark> ${this.escapeHtml(query)}</p><p><mark>A:</mark> ${placeholderAnswer}</p>`;
    results.prepend(item);
  };

  StoryEngine.prototype.updateInlineNav = function() {
    const idx = this.scenes.findIndex(s => s.id === this.currentSceneId);
    const prevLink = document.getElementById('scene-nav-prev');
    const nextLink = document.getElementById('scene-nav-next');
    if (prevLink) prevLink.classList.toggle('disabled', idx <= 0);
    if (nextLink) nextLink.classList.toggle('disabled', idx < 0 || idx >= this.scenes.length - 1);
  };

  StoryEngine.prototype.navigateRelativeScene = function(delta) {
    const idx = this.scenes.findIndex(s => s.id === this.currentSceneId);
    const newIdx = idx + delta;
    if (newIdx < 0 || newIdx >= this.scenes.length) return;
    this.editScene(this.scenes[newIdx].id);
  };

  StoryEngine.prototype.markSceneDirty = function() {
    this._sceneDirty = true;
    const status = document.getElementById('scene-save-status');
    if (status) status.textContent = 'Unsaved changes';
  };

  StoryEngine.prototype.debounceSceneSave = function() {
    clearTimeout(this._sceneSaveTimer);
    this._sceneSaveTimer = setTimeout(() => this.saveSceneChanges(), 1200);
  };

  StoryEngine.prototype.saveSceneChanges = async function() {
    if (!this.currentSceneId) return;
    const titleEl = document.getElementById('scene-title');
    const locationEl = document.getElementById('scene-location');
    const payload = {};
    if (titleEl) payload.title = titleEl.textContent.trim();
    if (locationEl) payload.location_id = locationEl.value || null;
    if (Object.keys(payload).length === 0) return;
    try {
      const res = await this.api.put(`/api/v1/scenes/${this.currentSceneId}`, payload);
      this._sceneDirty = false;
      const status = document.getElementById('scene-save-status');
      if (status) status.textContent = 'Saved';
      console.log('💾 Scene saved', res);
    } catch (e) {
      console.error('Scene save failed', e);
      const status = document.getElementById('scene-save-status');
      if (status) status.textContent = 'Save failed';
    }
  };

  StoryEngine.prototype.addBlock = async function(type) {
    if (!this.currentSceneId) return;
    const currentBlocks = Array.from(document.querySelectorAll('#scene-content details[data-block-id]'));
    const order = currentBlocks.length;
    const blockData = { block_type: type, order, content: '' };
    try {
      const resp = await this.api.post(`/api/v1/scenes/${this.currentSceneId}/blocks`, blockData);
      const newBlock = resp.data?.block || resp.block || resp.data;
      await this.loadSceneIntoEditor(this.currentSceneId);
      console.log('➕ Block added', newBlock);
    } catch (e) { console.error('Failed to add block', e); }
  };

  StoryEngine.prototype.markBlockDirty = function(blockId) {
    if (!this._dirtyBlocks) this._dirtyBlocks = new Set();
    this._dirtyBlocks.add(blockId);
  };

  StoryEngine.prototype.debounceBlockSave = function(blockId, detailsEl) {
    if (!this._debouncers) this._debouncers = {};
    clearTimeout(this._debouncers[blockId]);
    this._debouncers[blockId] = setTimeout(() => this.saveBlock(blockId, detailsEl), 1000);
  };

  StoryEngine.prototype.saveBlock = async function(blockId, detailsEl) {
    if (!this.currentSceneId) return;
    try {
      const blockType = detailsEl.getAttribute('data-block-type');
      let content = '';
      if (blockType === 'prose' || blockType === 'dialogue') {
        const ta = detailsEl.querySelector('textarea');
        if (ta) content = ta.value;
      } else if (blockType === 'milestone') {
        const inputs = detailsEl.querySelectorAll('input[type="text"]');
        const parts = Array.from(inputs).map(i => i.value.trim()).filter(Boolean);
        content = parts.join(' ');
      }
      const order = Array.from(detailsEl.parentElement.querySelectorAll('details[data-block-id]')).indexOf(detailsEl);
      const payload = { content, order };
      await this.api.put(`/api/v1/scenes/${this.currentSceneId}/blocks/${blockId}`, payload);
      console.log('💾 Block saved', blockId);
    } catch (e) { console.error('Failed to save block', blockId, e); }
  };

})();
