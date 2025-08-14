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

    async editScene(sceneId) {
        console.log(`✏️ Editing scene: ${sceneId}`);
        
        // Find the scene data for the breadcrumb
        const scene = this.scenes.find(s => s.id === sceneId);
        const sceneTitle = scene ? scene.title || 'Untitled Scene' : 'Scene';
        
        // Update breadcrumb
        const breadcrumbTitle = document.getElementById('scene-breadcrumb-title');
        if (breadcrumbTitle) {
            breadcrumbTitle.textContent = sceneTitle;
        }
        
        // Switch to scene editor
        if (window.pageLoader) {
            window.pageLoader.loadPage('scene-editor');
        }
        
        // TODO: Load scene blocks and full scene data
    }

    async deleteScene(sceneId) {
        if (!confirm('Are you sure you want to delete this scene?')) return;
        
        try {
            console.log(`🗑️ Deleting scene: ${sceneId}`);
            
            const { error } = await this.supabase
                .from('scenes')
                .delete()
                .eq('id', sceneId);

            if (error) throw error;

            // Refresh scenes list
            await this.loadScenes();
            this.updateScenesCount();
            
            console.log('✅ Scene deleted successfully');
        } catch (error) {
            console.error('❌ Failed to delete scene:', error);
            this.showError('Failed to delete scene: ' + error.message);
        }
    }

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


    async createScene() {
        try {
            const title = prompt('Scene title:');
            if (!title) return;

            const { data, error } = await this.supabase
                .from('scenes')
                .insert([
                    {
                        title: title,
                        timestamp: 1000
                    }
                ])
                .select()
                .single();

            if (error) throw error;

            console.log('✅ Scene created via Supabase:', data);
            await this.loadScenes(); // Refresh list
        } catch (error) {
            console.error('Failed to create scene:', error);
            alert('Failed to create scene: ' + error.message);
        }
    }

    async createEntity() {
        try {
            const name = prompt('Entity name:');
            if (!name) return;

            const { data, error } = await this.supabase
                .from('entities')
                .insert([
                    {
                        name: name,
                        entity_type: 'character',
                        description: 'New entity created from frontend'
                    }
                ])
                .select()
                .single();

            if (error) throw error;

            console.log('✅ Entity created via Supabase:', data);
            await this.loadEntities(); // Refresh list
        } catch (error) {
            console.error('Failed to create entity:', error);
            alert('Failed to create entity: ' + error.message);
        }
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
        row.onclick = () => window.storyEngine.editScene(scene.id);
        
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
        // Update scene header
        this.updateElement('scene-title', scene.title || 'Untitled Scene');
        this.updateElement('scene-timestamp', scene.timestamp || '1');
        this.updateElement('scene-id', scene.id);
        
        // Render entity tags
        this.renderEntityTags(entities);
        
        // Render scene blocks
        this.renderSceneBlocks(blocks);
        
        console.log('✅ Scene rendered successfully');
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
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.storyEngine = new StoryEngine();
});

