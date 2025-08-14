/**
 * QuantumMateria Story Engine - Frontend Application
 * Hybrid architecture: Supabase direct calls + FastAPI commands
 */

class StoryEngine {
    constructor() {
        this.supabase = null;
        this.config = null;
        this.api = new ApiClient();
        this.scenes = [];
        this.entitiesPreview = []; // restored: holds lightweight entity list
        this.pendingSceneId = null; // Used when navigating to scene-editor page
        this.init();
    }

    async init() {
        try {
            // Load configuration from FastAPI
            await this.loadConfig();
            
            // Initialize Supabase client
            this.initSupabase();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadInitialData();
            
            console.log('✅ Story Engine initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Story Engine:', error);
            this.showError('Failed to initialize application: ' + error.message);
        }
    }

    async loadConfig() {
        // Use local Supabase credentials from 'supabase status'
        this.config = {
            supabase_url: 'http://127.0.0.1:54321',
            supabase_anon_key: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
        };
    }

    initSupabase() {
        const { createClient } = supabase;
        this.supabase = createClient(
            this.config.supabase_url,
            this.config.supabase_anon_key
        );
    }

    setupEventListeners() {
        // Demo buttons
        document.getElementById('demo-supabase')?.addEventListener('click', 
            () => this.demoSupabaseDirect());
        document.getElementById('demo-fastapi')?.addEventListener('click', 
            () => this.demoFastApiCommand());
        
        // Create buttons
        document.getElementById('create-scene-btn')?.addEventListener('click', 
            () => this.createScene());
        document.getElementById('create-entity-btn')?.addEventListener('click', 
            () => this.createEntity());
        
        // Tool buttons
        document.getElementById('expand-all')?.addEventListener('click', 
            () => this.expandAll());
        document.getElementById('collapse-all')?.addEventListener('click', 
            () => this.collapseAll());
            
        // Page loading integration
        // Event handlers will be attached by PageLoader when pages are loaded
    }


    updateScenesCount() {
        const countElement = document.getElementById('scenes-count');
        if (countElement && this.scenes) {
            const count = this.scenes.length;
            countElement.textContent = `${count} ${count === 1 ? 'scene' : 'scenes'}`;
        }
    }

    async loadInitialData() {
        // Load system health from FastAPI
        await this.checkSystemHealth();
        
        // Load data but don't render until needed
        // Data will be rendered when pages are loaded
        await Promise.all([
            this.loadScenesData(),
            this.loadEntitiesData(),
        ]);
    }

    // =================================================================
    // SUPABASE DIRECT OPERATIONS (Tier 0)
    // =================================================================

    async loadScenesData() {
        try {
            const { data, error } = await this.supabase
                .from('scenes')
                .select('id, title, timestamp, created_at, location_id')
                .order('timestamp', { ascending: true });

            if (error) throw error;

            this.scenes = data || [];
            console.log('✅ Scenes data loaded:', this.scenes.length);
        } catch (error) {
            console.error('❌ Failed to load scenes data:', error);
            this.showError('Failed to load scenes: ' + error.message);
        }
    }

    async loadScenes() {
        await this.loadScenesData();
        this.renderScenesGrid(this.scenes);
    }

    // Restored entity loading methods
    async loadEntitiesData() {
        try {
            const { data, error } = await this.supabase
                .from('entities')
                .select('id, name, entity_type, description')
                .order('name')
                .limit(10);
            if (error) throw error;
            this.entitiesPreview = data || [];
            console.log('✅ Entities data loaded:', this.entitiesPreview.length);
        } catch (error) {
            console.error('❌ Failed to load entities data:', error);
        }
    }

    async loadEntities() {
        await this.loadEntitiesData();
        this.renderEntitiesList(this.entitiesPreview);
    }

    async editScene(sceneId) {
        // Navigate to scene editor (page-loader will call initialization hooks)
        this.pendingSceneId = sceneId;
        if (window.pageLoader) {
            window.pageLoader.loadPage('scene-editor');
        } else {
            console.warn('pageLoader not ready; fallback to legacy selectScene');
            await this.selectScene(sceneId);
        }
    }

    // Load a scene into the editor page after it is inserted into DOM
    async loadSceneIntoEditor(sceneId) {
        try {
            console.log('📝 Loading scene into editor:', sceneId);
            // Ensure scenes list is available
            if (!this.scenes || this.scenes.length === 0) {
                await this.loadScenesData();
            }
            // Fetch full scene record
            const { data: scene, error } = await this.supabase
                .from('scenes')
                .select('*')
                .eq('id', sceneId)
                .single();
            if (error) throw error;
            // Fetch blocks (FastAPI) & entities (placeholder)
            let blocks = [];
            try {
                const blocksResp = await this.api.getSceneBlocks(sceneId);
                blocks = blocksResp.data?.blocks || [];
            } catch (e) {
                console.warn('Blocks load failed (placeholder endpoint?)', e);
            }
            let entities = [];
            try {
                const entsResp = await this.api.getSceneEntities(sceneId);
                entities = entsResp.data?.entities || [];
            } catch (e) {
                console.warn('Entities load failed (placeholder endpoint?)', e);
            }
            // Render core content
            this.renderScene(scene, blocks, entities);
            // Breadcrumb
            const crumb = document.getElementById('scene-breadcrumb-title');
            if (crumb) crumb.textContent = scene.title || 'Untitled Scene';
            // Populate metadata selects
            this.populateSceneMetadata(sceneId, scene);
            // Attach handlers (idempotent)
            this.attachSceneEditorHandlers();
        } catch (err) {
            console.error('Failed to load scene into editor:', err);
            this.updateElement('scene-content', `<p class="error">Failed to load scene: ${this.escapeHtml(err.message)}</p>`);
        }
    }

    populateSceneMetadata(sceneId, scene) {
        // Location select (using existing scenes' location_ids as provisional list)
        const locSelect = document.getElementById('scene-location');
        if (locSelect) {
            const uniqueLocations = Array.from(new Set(this.scenes.map(s => s.location_id).filter(Boolean)));
            locSelect.innerHTML = '<option value="">Select location...</option>' +
                uniqueLocations.map(loc => `<option value="${this.escapeHtml(loc)}">${this.escapeHtml(loc)}</option>`).join('');
            if (scene.location_id) locSelect.value = scene.location_id;
        }
        // Previous / Next selects
        const prevSelect = document.getElementById('scene-previous');
        const nextSelect = document.getElementById('scene-next');
        if (prevSelect && nextSelect) {
            const index = this.scenes.findIndex(s => s.id === sceneId);
            const before = this.scenes.slice(0, index);
            const after = this.scenes.slice(index + 1);
            prevSelect.innerHTML = '<option value="">None</option>' + before.map(s => `<option value="${s.id}">${this.escapeHtml(s.title || 'Untitled')}</option>`).join('');
            nextSelect.innerHTML = '<option value="">None</option>' + after.map(s => `<option value="${s.id}">${this.escapeHtml(s.title || 'Untitled')}</option>`).join('');
            // Preselect immediate neighbors if exist
            if (before.length) prevSelect.value = before[before.length - 1].id;
            if (after.length) nextSelect.value = after[0].id;
        }
    }

    attachSceneEditorHandlers() {
        if (this._sceneEditorHandlersAttached) return;
        // Continuity analysis
        document.getElementById('run-continuity')?.addEventListener('click', () => this.runContinuityAnalysis());
        // World query form
        const wqForm = document.getElementById('world-query-form');
        const wqInput = document.getElementById('world-query-input');
        if (wqForm && wqInput) {
            wqForm.addEventListener('submit', e => {
                e.preventDefault();
                const q = wqInput.value.trim();
                if (!q) return;
                this.queryWorld(q);
                wqInput.value = '';
            });
        }
        // Add block buttons
        document.getElementById('add-prose')?.addEventListener('click', () => this.addBlock('prose'));
        document.getElementById('add-dialogue')?.addEventListener('click', () => this.addBlock('dialogue'));
        document.getElementById('add-milestone')?.addEventListener('click', () => this.addBlock('milestone'));
        // Save button
        document.getElementById('save-scene-btn')?.addEventListener('click', () => this.saveSceneChanges());
        // Scene title autosave
        const titleEl = document.getElementById('scene-title');
        if (titleEl) {
            titleEl.addEventListener('input', () => {
                this.markSceneDirty();
                this.debounceSceneSave();
            });
        }
        // Location change
        document.getElementById('scene-location')?.addEventListener('change', () => {
            this.markSceneDirty();
            this.saveSceneChanges();
        });
        // Navigation links
        document.getElementById('scene-nav-list')?.addEventListener('click', e => { e.preventDefault(); window.pageLoader?.loadPage('scenes'); });
        document.getElementById('scene-nav-prev')?.addEventListener('click', e => { e.preventDefault(); this.navigateRelativeScene(-1); });
        document.getElementById('scene-nav-next')?.addEventListener('click', e => { e.preventDefault(); this.navigateRelativeScene(1); });
        // Delegate block content autosave
        document.getElementById('scene-content')?.addEventListener('input', (e) => {
            const target = e.target;
            if (target.tagName === 'TEXTAREA' || (target.tagName === 'INPUT' && target.type === 'text')) {
                const details = target.closest('details[data-block-id]');
                if (details) {
                    const blockId = details.getAttribute('data-block-id');
                    this.markBlockDirty(blockId);
                    this.debounceBlockSave(blockId, details);
                }
            }
        });
        // Debouncers
        this._debouncers = {};
        this._sceneEditorHandlersAttached = true;
    }

    runContinuityAnalysis() {
        const container = document.querySelector('#continuity-analysis .continuity-body');
        if (!container) return;
        container.innerHTML = '<p><span aria-busy="true">Analyzing continuity...</span></p>';
        const sceneIdEl = document.getElementById('scene-id');
        const sceneId = sceneIdEl ? sceneIdEl.textContent : '';
        // Placeholder async simulation
        setTimeout(() => {
            container.innerHTML = `
                <p><strong>Summary:</strong> No inconsistencies detected.</p>
                <p><small>Scene ${this.escapeHtml(sceneId)} passes baseline checks (placeholder).</small></p>`;
        }, 800);
    }

    queryWorld(query) {
        const results = document.getElementById('world-query-results');
        if (!results) return;
        const sceneId = document.getElementById('scene-id')?.textContent || '';
        const ts = new Date().toLocaleTimeString();
        const placeholderAnswer = `Stub answer for "${this.escapeHtml(query)}" (integrate /api/search or knowledge soon).`;
        const item = document.createElement('div');
        item.className = 'query-item';
        item.innerHTML = `<p><strong>${ts}</strong> <mark>Q:</mark> ${this.escapeHtml(query)}</p><p><mark>A:</mark> ${placeholderAnswer}</p>`;
        results.prepend(item);
    }

    // =================================================================
    // FASTAPI COMMAND OPERATIONS (Tier 1 & 2)
    // =================================================================

    async checkSystemHealth() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            this.renderSystemStatus(health);
        } catch (error) {
            console.error('Failed to check system health:', error);
            this.updateElement('system-status', 
                '<p class="error">System health check failed</p>');
        }
    }

    async fastApiCommand(endpoint, data = null) {
        try {
            const options = {
                method: data ? 'POST' : 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(endpoint, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'API request failed');
            }

            return result;
        } catch (error) {
            console.error('FastAPI command failed:', error);
            throw error;
        }
    }

    // =================================================================
    // DEMO FUNCTIONS
    // =================================================================

    async demoSupabaseDirect() {
        this.updateDemoOutput('🔄 Testing Supabase direct call...\n');
        
        try {
            // Direct count query to Supabase
            const { count, error } = await this.supabase
                .from('scenes')
                .select('*', { count: 'exact', head: true });

            if (error) throw error;

            const output = `✅ Supabase Direct Call Success!
Method: Direct table query via supabase-js client
Endpoint: scenes table
Result: Found ${count || 0} scenes in database
Architecture: Frontend → Supabase (no FastAPI involved)
Benefits: Real-time subscriptions, zero server overhead

Table Schema Used:
- scenes: id, title, timestamp, created_at
- entities: id, name, entity_type, description  
- story_goals: id, description, verb, created_at`;

            this.updateDemoOutput(output);
        } catch (error) {
            this.updateDemoOutput(`❌ Supabase direct call failed: ${error.message}`);
        }
    }

    async demoFastApiCommand() {
        this.updateDemoOutput('🔄 Testing FastAPI command call...\n');
        
        try {
            // Call FastAPI health endpoint as example command
            const result = await this.fastApiCommand('/health');

            const output = `✅ FastAPI Command Success!
Method: HTTP request to FastAPI endpoint
Endpoint: /health
Result: ${JSON.stringify(result, null, 2)}
Architecture: Frontend → FastAPI → Supabase
Benefits: Business logic, validation, complex operations`;

            this.updateDemoOutput(output);
        } catch (error) {
            this.updateDemoOutput(`❌ FastAPI command failed: ${error.message}`);
        }
    }

    // =================================================================
    // UI RENDERING HELPERS
    // =================================================================

    renderScenesGrid(scenes) {
        const tbody = document.getElementById('scenes-table-body');
        if (!tbody) {
            console.warn('⚠️ scenes-table-body element not found - page not loaded yet');
            return;
        }

        // Clear existing content
        tbody.innerHTML = '';

        if (scenes.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.style.textAlign = 'center';
            cell.style.padding = '3rem';
            
            const article = document.createElement('article');
            
            const header = document.createElement('header');
            const title = document.createElement('h3');
            title.textContent = 'No scenes found';
            header.appendChild(title);
            
            const description = document.createElement('p');
            description.textContent = 'Create your first scene to begin telling your story.';
            
            const footer = document.createElement('footer');
        const button = document.createElement('button');
            button.textContent = '+ Create Scene';
            button.onclick = () => window.storyEngine.createScene();
            footer.appendChild(button);
            
            article.appendChild(header);
            article.appendChild(description);
            article.appendChild(footer);
            cell.appendChild(article);
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }

        // Create rows using DOM manipulation
        scenes.forEach(scene => {
            const row = this.createSceneRow(scene);
            tbody.appendChild(row);
        });
        
        console.log(`✅ Rendered ${scenes.length} scenes`);
    }

    createSceneRow(scene) {
        const row = document.createElement('tr');
        row.dataset.id = scene.id;
        row.onclick = () => this.editScene(scene.id);

        // Timeline cell
        const timestampCell = document.createElement('td');
        timestampCell.textContent = scene.timestamp ? `Day ${scene.timestamp}` : 'No timestamp';
        
        // Title cell
        const titleCell = document.createElement('td');
        titleCell.textContent = scene.title || 'Untitled Scene';
        
        // Location cell
        const locationCell = document.createElement('td');
        locationCell.textContent = scene.location_id || 'No location';
        
        // Created date cell
        const createdCell = document.createElement('td');
        createdCell.textContent = new Date(scene.created_at).toLocaleDateString();
        
        // Actions cell
        const actionsCell = document.createElement('td');
        
        const editButton = document.createElement('button');
        editButton.textContent = 'Edit';
        editButton.onclick = (e) => {
            e.stopPropagation();
            window.storyEngine.editScene(scene.id);
        };
        
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.onclick = (e) => {
            e.stopPropagation();
            window.storyEngine.deleteScene(scene.id);
        };
        
        actionsCell.appendChild(editButton);
        actionsCell.appendChild(deleteButton);
        
        // Assemble row
        row.appendChild(timestampCell);
        row.appendChild(titleCell);
        row.appendChild(locationCell);
        row.appendChild(createdCell);
        row.appendChild(actionsCell);
        
        return row;
    }

    renderEntitiesList(entities) {
        const container = document.getElementById('entities-list');
        if (!container) {
            console.warn('⚠️ entities-list element not found - page not loaded yet');
            return;
        }
        
        // Clear existing content
        container.innerHTML = '';
        
        if (entities.length === 0) {
            const emptyMessage = document.createElement('p');
            const em = document.createElement('em');
            em.textContent = 'No entities yet';
            emptyMessage.appendChild(em);
            container.appendChild(emptyMessage);
            return;
        }

        // Create entity articles using DOM manipulation
        entities.forEach(entity => {
            const article = document.createElement('article');
            article.dataset.id = entity.id;
            
            const header = document.createElement('header');
            const strong = document.createElement('strong');
            strong.textContent = entity.name;
            header.appendChild(strong);
            
            const small = document.createElement('small');
            small.textContent = entity.entity_type;
            
            article.appendChild(header);
            article.appendChild(small);
            container.appendChild(article);
        });
        
        console.log(`✅ Rendered ${entities.length} entities in dashboard`);
    }


    renderSystemStatus(health) {
        const container = document.getElementById('system-status');
        if (!container) {
            console.error('❌ system-status element not found');
            return;
        }
        
        // Clear existing content
        container.innerHTML = '';
        
        const isHealthy = health.status === 'healthy';
        
        const statusDiv = document.createElement('div');
        if (!isHealthy) {
            statusDiv.setAttribute('role', 'alert');
        }
        
        // Status
        const statusP = document.createElement('p');
        statusP.innerHTML = '<strong>Status:</strong> ';
        const statusMark = document.createElement('mark');
        statusMark.className = isHealthy ? 'valid' : 'invalid';
        statusMark.textContent = health.status;
        statusP.appendChild(statusMark);
        
        // Database
        const dbP = document.createElement('p');
        dbP.innerHTML = `<strong>Database:</strong> ${health.database}`;
        
        // Entities
        const entitiesP = document.createElement('p');
        entitiesP.innerHTML = `<strong>Entities:</strong> ${health.entity_count || 0}`;
        
        // Knowledge
        const knowledgeP = document.createElement('p');
        knowledgeP.innerHTML = `<strong>Knowledge:</strong> ${health.knowledge_snapshot_count || 0}`;
        
        statusDiv.appendChild(statusP);
        statusDiv.appendChild(dbP);
        statusDiv.appendChild(entitiesP);
        statusDiv.appendChild(knowledgeP);
        
        container.appendChild(statusDiv);
        
        console.log(`✅ System status rendered: ${health.status}`);
    }

    updateDemoOutput(text) {
        this.updateElement('demo-output', text);
    }

    updateElement(id, html) {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = html;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        console.error(message);
        alert(message);
    }

    // =================================================================
    // SCENE EDITOR FUNCTIONALITY
    // =================================================================

    async selectScene(sceneId) {
        try {
            console.log('🎬 Loading scene:', sceneId);
            
            // Show loading state
            this.showWelcomeState(false);
            this.showSceneEditor(true);
            this.updateElement('scene-content', '<div class="loading-blocks">Loading scene content...</div>');
            
            // Highlight selected scene in navigation
            this.highlightSelectedScene(sceneId);
            
            // Load scene data from Supabase
            const { data: scene, error } = await this.supabase
                .from('scenes')
                .select('*')
                .eq('id', sceneId)
                .single();

            if (error) throw error;

            // Load scene blocks via FastAPI (since it has complex content operations)
            const blocks = await this.api.getSceneBlocks(sceneId);
            
            // Load related entities
            const entities = await this.api.getSceneEntities(sceneId);
            
            // Render the scene
            this.renderScene(scene, blocks.data?.blocks || [], entities.data?.entities || []);
            
        } catch (error) {
            console.error('Failed to load scene:', error);
            this.updateElement('scene-content', 
                '<div class="error">Failed to load scene: ' + error.message + '</div>');
        }
    }

    showWelcomeState(show) {
        const welcomeState = document.getElementById('welcome-state');
        if (welcomeState) {
            welcomeState.hidden = !show;
        }
    }

    showSceneEditor(show) {
        const sceneEditor = document.getElementById('scene-editor');
        if (sceneEditor) {
            sceneEditor.hidden = !show;
        }
    }

    highlightSelectedScene(sceneId) {
        // Remove previous selection
        document.querySelectorAll('tr[data-id]').forEach(item => {
            item.removeAttribute('aria-current');
        });
        
        // Highlight new selection
        const selectedItem = document.querySelector(`tr[data-id="${sceneId}"]`);
        if (selectedItem) {
            selectedItem.setAttribute('aria-current', 'true');
        }
    }

    renderScene(scene, blocks, entities) {
        this.currentSceneId = scene.id; // track current
        // Update scene header
        this.updateElement('scene-title', scene.title || 'Untitled Scene');
        this.updateElement('scene-timestamp', scene.timestamp || '1');
        this.updateElement('scene-id', scene.id);
        
        // Render entity tags
        this.renderEntityTags(entities);
        
        // Render scene blocks
        this.renderSceneBlocks(blocks);
        
        this.updateInlineNav();

        console.log('✅ Scene rendered successfully');
    }

    // Inline navigation update
    updateInlineNav() {
        const idx = this.scenes.findIndex(s => s.id === this.currentSceneId);
        const prevLink = document.getElementById('scene-nav-prev');
        const nextLink = document.getElementById('scene-nav-next');
        if (prevLink) prevLink.classList.toggle('disabled', idx <= 0);
        if (nextLink) nextLink.classList.toggle('disabled', idx < 0 || idx >= this.scenes.length - 1);
    }

    navigateRelativeScene(delta) {
        const idx = this.scenes.findIndex(s => s.id === this.currentSceneId);
        const newIdx = idx + delta;
        if (newIdx < 0 || newIdx >= this.scenes.length) return;
        this.editScene(this.scenes[newIdx].id);
    }

    renderEntityTags(entities) {
        if (!entities || entities.length === 0) {
            this.updateElement('linked-entities', '<p><em>No linked entities</em></p>');
            return;
        }

        const html = entities.map(entity => `
            <kbd data-tooltip="${entity.entity_type}" data-id="${entity.id}">
                ${this.escapeHtml(entity.name)}
            </kbd>
        `).join(' ');

        this.updateElement('linked-entities', html);
    }

    renderSceneBlocks(blocks) {
        if (!blocks || blocks.length === 0) {
            this.updateElement('scene-content', `
                <article>
                    <header>
                        <h3>Empty Scene</h3>
                    </header>
                    <p>This scene has no content blocks yet. Use the buttons below to add prose, dialogue, or milestones.</p>
                </article>
            `);
            return;
        }

        const html = blocks.map((block, index) => this.renderBlock(block, index)).join('');
        this.updateElement('scene-content', html);
    }

    renderBlock(block, index) {
        const blockId = block.id || `block-${index}`;
        const blockType = block.block_type || 'prose';
        const content = block.content || '';
        
        let blockContent = '';
        let preview = '';
        
        switch (blockType) {
            case 'prose':
                preview = content.substring(0, 50) + (content.length > 50 ? '...' : '');
                blockContent = `
                    <div class="prose-content">
                        <textarea placeholder="Write your prose here...">${this.escapeHtml(content)}</textarea>
                    </div>
                `;
                break;
                
            case 'dialogue':
                preview = content.substring(0, 50) + (content.length > 50 ? '...' : '');
                blockContent = `
                    <fieldset>
                        <legend>Participants</legend>
                        <div role="group">
                            <label for="speaker-${blockId}">Speaker:</label>
                            <select id="speaker-${blockId}">
                                <option value="">Select character...</option>
                            </select>
                            <label for="listener-${blockId}">Listener:</label>
                            <select id="listener-${blockId}">
                                <option value="">Select character...</option>
                            </select>
                        </div>
                        <textarea placeholder="Write dialogue here...">${this.escapeHtml(content)}</textarea>
                    </fieldset>
                `;
                break;
                
            case 'milestone':
                const subject = block.subject || '';
                const verb = block.verb || 'discovers';
                const object = block.object || '';
                preview = `${subject} ${verb} ${object}`.trim();
                blockContent = `
                    <fieldset>
                        <legend>Milestone Structure</legend>
                        <div class="grid">
                            <label>
                                Subject
                                <input type="text" value="${this.escapeHtml(subject)}" placeholder="Who or what">
                            </label>
                            <div style="display: flex; align-items: end; justify-content: center;">
                                <mark>${verb}</mark>
                            </div>
                            <label>
                                Object
                                <input type="text" value="${this.escapeHtml(object)}" placeholder="What happens">
                            </label>
                        </div>
                    </fieldset>
                `;
                break;
        }

        return `
            <details open data-block-id="${blockId}" data-block-type="${blockType}">
                <summary>
                    <hgroup>
                        <h4><mark>${blockType}</mark></h4>
                        <p>${preview}</p>
                    </hgroup>
                    <div role="group">
                        <button onclick="event.stopPropagation(); window.storyEngine.moveBlockUp('${blockId}')" title="Move up" class="secondary outline">↑</button>
                        <button onclick="event.stopPropagation(); window.storyEngine.moveBlockDown('${blockId}')" title="Move down" class="secondary outline">↓</button>
                        <button onclick="event.stopPropagation(); window.storyEngine.editBlock('${blockId}')" title="Edit" class="secondary outline">✎</button>
                        <button onclick="event.stopPropagation(); window.storyEngine.deleteBlock('${blockId}')" title="Delete" class="secondary outline">✕</button>
                    </div>
                </summary>
                <div>
                    ${blockContent}
                </div>
            </details>
        `;
    }

    // Placeholder block control methods
    moveBlockUp(blockId) {
        console.log('🔧 Move block up:', blockId);
    }

    moveBlockDown(blockId) {
        console.log('🔧 Move block down:', blockId);
    }

    editBlock(blockId) {
        console.log('🔧 Edit block:', blockId);
    }

    deleteBlock(blockId) {
        console.log('🔧 Delete block:', blockId);
    }

    // Placeholder functions for tools
    expandAll() {
        document.querySelectorAll('.scene-block').forEach(block => {
            block.open = true;
        });
    }

    collapseAll() {
        document.querySelectorAll('.scene-block').forEach(block => {
            block.open = false;
        });
    }

    // Scene save logic
    markSceneDirty() {
        this._sceneDirty = true;
        const status = document.getElementById('scene-save-status');
        if (status) status.textContent = 'Unsaved changes';
    }

    debounceSceneSave() {
        clearTimeout(this._sceneSaveTimer);
        this._sceneSaveTimer = setTimeout(() => this.saveSceneChanges(), 1200);
    }

    async saveSceneChanges() {
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
    }

    // Block creation
    async addBlock(type) {
        if (!this.currentSceneId) return;
        const currentBlocks = Array.from(document.querySelectorAll('#scene-content details[data-block-id]'));
        const order = currentBlocks.length;
        const blockData = { block_type: type, order, content: '' };
        try {
            const resp = await this.api.post(`/api/v1/scenes/${this.currentSceneId}/blocks`, blockData);
            const newBlock = resp.data?.block || resp.block || resp.data; // flexible handling
            // Fetch blocks again for accurate ordering
            await this.loadSceneIntoEditor(this.currentSceneId);
            console.log('➕ Block added', newBlock);
        } catch (e) {
            console.error('Failed to add block', e);
        }
    }

    // Block autosave
    markBlockDirty(blockId) {
        if (!this._dirtyBlocks) this._dirtyBlocks = new Set();
        this._dirtyBlocks.add(blockId);
    }
    debounceBlockSave(blockId, detailsEl) {
        if (!this._debouncers) this._debouncers = {};
        clearTimeout(this._debouncers[blockId]);
        this._debouncers[blockId] = setTimeout(() => this.saveBlock(blockId, detailsEl), 1000);
    }
    async saveBlock(blockId, detailsEl) {
        if (!this.currentSceneId) return;
        try {
            // Determine block type
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
        } catch (e) {
            console.error('Failed to save block', blockId, e);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.storyEngine = new StoryEngine();
});
