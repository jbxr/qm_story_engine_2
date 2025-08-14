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
        document.getElementById('create-goal-btn')?.addEventListener('click', 
            () => this.createGoal());
        
        // Tool buttons
        document.getElementById('expand-all')?.addEventListener('click', 
            () => this.expandAll());
        document.getElementById('collapse-all')?.addEventListener('click', 
            () => this.collapseAll());
            
        // View switching - Wire up "Manage Entities" button
        document.querySelector('button[onclick*="entities"]')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showView('entity-manager');
        });
    }

    // =================================================================
    // VIEW SWITCHING - Simple show/hide logic for SPA
    // =================================================================
    
    showView(viewName) {
        // Hide all views
        const views = ['welcome-state', 'scenes-list', 'scene-editor', 'entity-manager'];
        views.forEach(view => {
            const element = document.getElementById(view);
            if (element) {
                element.style.display = 'none';
                element.classList.remove('active');
            }
        });
        
        // Show target view
        const targetView = document.getElementById(viewName);
        if (targetView) {
            const displayType = ['entity-manager', 'scenes-list'].includes(viewName) ? 'flex' : 'block';
            targetView.style.display = displayType;
            targetView.classList.add('active');
            
            // Initialize managers if needed
            if (viewName === 'entity-manager' && window.entityManager) {
                window.entityManager.loadEntities();
            } else if (viewName === 'scenes-list') {
                this.loadScenes();
                this.updateScenesCount();
            }
        }
        
        // Update navigation active state
        this.updateNavActiveState(viewName);
        
        console.log(`📱 Switched to view: ${viewName}`);
    }
    
    updateNavActiveState(viewName) {
        // Remove active state from all nav links
        document.querySelectorAll('aside nav a').forEach(item => {
            item.removeAttribute('aria-current');
        });
        
        // Add active state based on current view
        let activeNavIndex = 0; // Dashboard by default
        if (viewName === 'scenes-list' || viewName === 'scene-editor') activeNavIndex = 1; // Scenes
        else if (viewName === 'entity-manager') activeNavIndex = 2; // Entities
        
        const navLinks = document.querySelectorAll('aside nav a');
        if (navLinks[activeNavIndex]) {
            navLinks[activeNavIndex].setAttribute('aria-current', 'page');
        }
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
        
        // Load data via Supabase direct calls
        await Promise.all([
            this.loadScenes(),
            this.loadEntities(),
            this.loadGoals()
        ]);
    }

    // =================================================================
    // SUPABASE DIRECT OPERATIONS (Tier 0)
    // =================================================================

    async loadScenes() {
        try {
            const { data, error } = await this.supabase
                .from('scenes')
                .select('id, title, timestamp, created_at, location_id')
                .order('timestamp', { ascending: true });

            if (error) throw error;

            this.scenes = data || [];
            this.renderScenesGrid(this.scenes);
            console.log('✅ Scenes loaded:', this.scenes.length);
        } catch (error) {
            console.error('❌ Failed to load scenes:', error);
            this.showError('Failed to load scenes: ' + error.message);
        }
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
        this.showView('scene-editor');
        
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

    async loadEntities() {
        try {
            const { data, error } = await this.supabase
                .from('entities')
                .select('id, name, entity_type, description')
                .order('name')
                .limit(10);

            if (error) throw error;

            this.renderEntitiesList(data || []);
        } catch (error) {
            console.error('Failed to load entities:', error);
            this.updateElement('entities-list', 
                '<p class="error">Failed to load entities</p>');
        }
    }

    async loadGoals() {
        try {
            const { data, error } = await this.supabase
                .from('story_goals')
                .select('id, description, verb, created_at')
                .order('created_at', { ascending: false })
                .limit(10);

            if (error) throw error;

            this.renderGoalsList(data || []);
        } catch (error) {
            console.error('Failed to load goals:', error);
            this.updateElement('goals-list', 
                '<p class="error">Failed to load goals</p>');
        }
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

    async createGoal() {
        try {
            const description = prompt('Goal description:');
            if (!description) return;

            const { data, error } = await this.supabase
                .from('story_goals')
                .insert([
                    {
                        description: description,
                        verb: 'achieve'
                    }
                ])
                .select()
                .single();

            if (error) throw error;

            console.log('✅ Goal created via Supabase:', data);
            await this.loadGoals(); // Refresh list
        } catch (error) {
            console.error('Failed to create goal:', error);
            alert('Failed to create goal: ' + error.message);
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
        if (!tbody) return;

        if (scenes.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state" style="text-align: center; padding: 3rem;">
                        <h3>No scenes found</h3>
                        <p>Create your first scene to begin telling your story.</p>
                        <button onclick="window.storyEngine.createScene()" class="primary-btn">
                            + Create Scene
                        </button>
                    </td>
                </tr>
            `;
            return;
        }

        const html = scenes.map(scene => this.renderSceneRow(scene)).join('');
        tbody.innerHTML = html;
    }

    renderSceneRow(scene) {
        const title = this.escapeHtml(scene.title || 'Untitled Scene');
        const location = scene.location_id || 'No location';
        const timestamp = scene.timestamp ? `Day ${scene.timestamp}` : 'No timestamp';
        const createdDate = new Date(scene.created_at).toLocaleDateString();

        return `
            <tr data-id="${scene.id}" onclick="window.storyEngine.editScene('${scene.id}')">
                <td class="scene-timestamp-cell">${timestamp}</td>
                <td class="scene-title-cell">${title}</td>
                <td class="scene-location-cell">${location}</td>
                <td>${createdDate}</td>
                <td class="scene-actions-cell">
                    <button onclick="event.stopPropagation(); window.storyEngine.editScene('${scene.id}')">
                        Edit
                    </button>
                    <button class="delete" onclick="event.stopPropagation(); window.storyEngine.deleteScene('${scene.id}')">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    }

    renderEntitiesList(entities) {
        if (entities.length === 0) {
            this.updateElement('entities-list', '<p class="empty">No entities yet</p>');
            return;
        }

        const html = entities.map(entity => `
            <div class="nav-item" data-id="${entity.id}">
                <strong>${this.escapeHtml(entity.name)}</strong>
                <small>${entity.entity_type}</small>
            </div>
        `).join('');

        this.updateElement('entities-list', html);
    }

    renderGoalsList(goals) {
        if (goals.length === 0) {
            this.updateElement('goals-list', '<p class="empty">No goals yet</p>');
            return;
        }

        const html = goals.map(goal => `
            <div class="nav-item" data-id="${goal.id}">
                <strong>${this.escapeHtml((goal.description || '').substring(0, 50))}...</strong>
                <small>${goal.verb || 'goal'}</small>
            </div>
        `).join('');

        this.updateElement('goals-list', html);
    }

    renderSystemStatus(health) {
        const statusClass = health.status === 'healthy' ? 'healthy' : 'unhealthy';
        const html = `
            <div class="status-${statusClass}">
                <p><strong>Status:</strong> ${health.status}</p>
                <p><strong>Database:</strong> ${health.database}</p>
                <p><strong>Entities:</strong> ${health.entity_count || 0}</p>
                <p><strong>Knowledge:</strong> ${health.knowledge_snapshot_count || 0}</p>
            </div>
        `;

        this.updateElement('system-status', html);
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
            welcomeState.style.display = show ? 'block' : 'none';
        }
    }

    showSceneEditor(show) {
        const sceneEditor = document.getElementById('scene-editor');
        if (sceneEditor) {
            sceneEditor.style.display = show ? 'flex' : 'none';
        }
    }

    highlightSelectedScene(sceneId) {
        // Remove previous selection
        document.querySelectorAll('.scene-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Highlight new selection
        const selectedItem = document.querySelector(`.scene-item[data-id="${sceneId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
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
            this.updateElement('linked-entities', '<p class="empty">No linked entities</p>');
            return;
        }

        const html = entities.map(entity => `
            <span class="entity-tag ${entity.entity_type}" data-id="${entity.id}">
                ${this.escapeHtml(entity.name)}
            </span>
        `).join('');

        this.updateElement('linked-entities', html);
    }

    renderSceneBlocks(blocks) {
        if (!blocks || blocks.length === 0) {
            this.updateElement('scene-content', `
                <div class="empty-scene">
                    <h3>Empty Scene</h3>
                    <p>This scene has no content blocks yet. Use the buttons below to add prose, dialogue, or milestones.</p>
                </div>
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
                    <div class="dialogue-content">
                        <div class="dialogue-participants">
                            <label>Speaker:</label>
                            <select>
                                <option value="">Select character...</option>
                            </select>
                            <label>Listener:</label>
                            <select>
                                <option value="">Select character...</option>
                            </select>
                        </div>
                        <textarea placeholder="Write dialogue here...">${this.escapeHtml(content)}</textarea>
                    </div>
                `;
                break;
                
            case 'milestone':
                const subject = block.subject || '';
                const verb = block.verb || 'discovers';
                const object = block.object || '';
                preview = `${subject} ${verb} ${object}`.trim();
                blockContent = `
                    <div class="milestone-content">
                        <div class="milestone-field">
                            <label>Subject</label>
                            <input type="text" value="${this.escapeHtml(subject)}" placeholder="Who or what">
                        </div>
                        <div class="milestone-verb">${verb}</div>
                        <div class="milestone-field">
                            <label>Object</label>
                            <input type="text" value="${this.escapeHtml(object)}" placeholder="What happens">
                        </div>
                    </div>
                `;
                break;
        }

        return `
            <details class="scene-block" open data-block-id="${blockId}" data-block-type="${blockType}">
                <summary class="block-header">
                    <div class="block-header-left">
                        <span class="block-type">${blockType}</span>
                        <span class="block-preview">${preview}</span>
                    </div>
                    <div class="block-controls">
                        <button class="block-control-btn" onclick="event.stopPropagation(); window.storyEngine.moveBlockUp('${blockId}')" title="Move up">↑</button>
                        <button class="block-control-btn" onclick="event.stopPropagation(); window.storyEngine.moveBlockDown('${blockId}')" title="Move down">↓</button>
                        <button class="block-control-btn" onclick="event.stopPropagation(); window.storyEngine.editBlock('${blockId}')" title="Edit">✎</button>
                        <button class="block-control-btn" onclick="event.stopPropagation(); window.storyEngine.deleteBlock('${blockId}')" title="Delete">✕</button>
                    </div>
                </summary>
                <div class="block-content">
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

// Add some basic styles for nav items
const style = document.createElement('style');
style.textContent = `
    /* Nav styles are now handled by Pico CSS semantic HTML */
    
    .empty, .error {
        color: var(--ink-3);
        font-style: italic;
        font-size: 0.8rem;
        margin: 0;
    }
    
    .error {
        color: #ff6b6b;
    }
    
    .status-healthy {
        color: #51cf66;
    }
    
    .status-unhealthy {
        color: #ff6b6b;
    }
`;
document.head.appendChild(style);