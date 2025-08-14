/**
 * Entity Management - CRUD Operations
 * Simple, focused implementation to prove basic workflows work
 */

class EntityManager {
    constructor() {
        this.api = new ApiClient();
        this.entities = [];
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.filters = {
            type: '',
            search: ''
        };
        this.editingEntity = null;
        this.initialized = false;
        
        this.init();
    }

    async init() {
        if (this.initialized) return; // Prevent double initialization
        
        try {
            console.log('🚀 Initializing Entity Manager...');
            
            this.setupEventListeners();
            await this.loadEntities();
            
            this.initialized = true;
            console.log('✅ Entity Manager initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Entity Manager:', error);
            this.showError('Failed to initialize application: ' + error.message);
        }
    }

    setupEventListeners() {
        // Create entity
        document.getElementById('create-entity-btn')?.addEventListener('click', 
            () => this.showCreateModal());
        
        // Form submission
        document.getElementById('entity-form')?.addEventListener('submit', 
            (e) => this.handleFormSubmit(e));
        
        // Modal controls
        document.getElementById('close-modal')?.addEventListener('click', 
            () => this.hideModal());
        document.getElementById('cancel-btn')?.addEventListener('click', 
            () => this.hideModal());
        
        // Delete modal controls
        document.getElementById('cancel-delete')?.addEventListener('click', 
            () => this.hideDeleteModal());
        document.getElementById('confirm-delete')?.addEventListener('click', 
            () => this.confirmDelete());
        
        // Filters
        document.getElementById('type-filter')?.addEventListener('change', 
            (e) => this.handleFilterChange('type', e.target.value));
        document.getElementById('search-input')?.addEventListener('input', 
            (e) => this.handleFilterChange('search', e.target.value));
        document.getElementById('clear-filters')?.addEventListener('click', 
            () => this.clearFilters());
        
        // Pagination
        document.getElementById('prev-page')?.addEventListener('click', 
            () => this.changePage(this.currentPage - 1));
        document.getElementById('next-page')?.addEventListener('click', 
            () => this.changePage(this.currentPage + 1));
        
        // Close modal on backdrop click
        document.getElementById('entity-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'entity-modal') {
                this.hideModal();
            }
        });
        
        document.getElementById('delete-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'delete-modal') {
                this.hideDeleteModal();
            }
        });
    }

    // =================================================================
    // DATA LOADING
    // =================================================================

    async loadEntities() {
        try {
            console.log('📡 Loading entities...', { 
                page: this.currentPage, 
                filters: this.filters 
            });
            
            this.showLoadingState();
            
            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageSize
            });
            
            if (this.filters.type) {
                params.append('entity_type', this.filters.type);
            }
            
            if (this.filters.search) {
                params.append('search', this.filters.search);
            }
            
            // Call API
            const response = await this.api.get(`/api/v1/entities?${params}`);
            const data = response.data || response;
            
            this.entities = data.entities || [];
            this.totalPages = Math.ceil((data.total || this.entities.length) / this.pageSize);
            
            console.log('✅ Entities loaded:', {
                count: this.entities.length,
                totalPages: this.totalPages
            });
            
            this.renderEntities();
            this.updatePagination();
            this.updateEntityCount();
            
        } catch (error) {
            console.error('❌ Failed to load entities:', error);
            this.showError('Failed to load entities: ' + error.message);
        }
    }

    // =================================================================
    // CRUD OPERATIONS
    // =================================================================

    async createEntity(entityData) {
        try {
            console.log('➕ Creating entity:', entityData);
            
            const response = await this.api.post('/api/v1/entities', entityData);
            console.log('📡 Raw API response:', response);
            
            // Handle the nested response structure: response.data.entity
            const newEntity = response.data?.entity || response.entity || response;
            
            console.log('✅ Entity created:', newEntity);
            
            // Validate the entity has required fields before adding to UI
            if (newEntity && newEntity.id && newEntity.name) {
                this.entities.unshift(newEntity);
                this.renderEntities();
                this.showSuccess('Entity created successfully!');
            } else {
                console.error('❌ Invalid entity structure:', newEntity);
                this.showError('Created entity but received invalid data structure');
                // Reload from server to get consistent state
                await this.loadEntities();
            }
            
            this.hideModal();
            
        } catch (error) {
            console.error('❌ Failed to create entity:', error);
            this.showError('Failed to create entity: ' + error.message);
        }
    }

    async updateEntity(entityId, entityData) {
        try {
            console.log('✏️ Updating entity:', entityId, entityData);
            
            const response = await this.api.put(`/api/v1/entities/${entityId}`, entityData);
            console.log('📡 Raw API response:', response);
            
            // Handle the nested response structure: response.data.entity
            const updatedEntity = response.data?.entity || response.entity || response;
            
            console.log('✅ Entity updated:', updatedEntity);
            
            // Validate the entity has required fields before updating UI
            if (updatedEntity && updatedEntity.id && updatedEntity.name) {
                // Update local list
                const index = this.entities.findIndex(e => e.id === entityId);
                if (index !== -1) {
                    this.entities[index] = updatedEntity;
                    this.renderEntities();
                    this.showSuccess('Entity updated successfully!');
                } else {
                    console.error('❌ Entity not found in local list:', entityId);
                    this.showError('Entity updated but not found in list');
                    // Reload from server to get consistent state
                    await this.loadEntities();
                }
            } else {
                console.error('❌ Invalid entity structure:', updatedEntity);
                this.showError('Updated entity but received invalid data structure');
                // Reload from server to get consistent state
                await this.loadEntities();
            }
            
            this.hideModal();
            
        } catch (error) {
            console.error('❌ Failed to update entity:', error);
            this.showError('Failed to update entity: ' + error.message);
        }
    }

    async deleteEntity(entityId) {
        try {
            console.log('🗑️ Deleting entity:', entityId);
            
            const response = await this.api.delete(`/api/v1/entities/${entityId}`);
            console.log('📡 Delete response:', response);
            
            // Verify the entity was deleted by checking it still exists in our local list
            const entityIndex = this.entities.findIndex(e => e.id === entityId);
            if (entityIndex !== -1) {
                // Remove from local list
                this.entities.splice(entityIndex, 1);
                this.renderEntities();
                
                console.log('✅ Entity deleted and removed from UI');
                this.showSuccess('Entity deleted successfully!');
            } else {
                console.warn('⚠️ Entity not found in local list during delete');
                // Still reload to ensure consistency
                await this.loadEntities();
            }
            
            this.hideDeleteModal();
            
        } catch (error) {
            console.error('❌ Failed to delete entity:', error);
            this.showError('Failed to delete entity: ' + error.message);
            this.hideDeleteModal();
        }
    }

    // =================================================================
    // UI RENDERING
    // =================================================================

    renderEntities() {
        const container = document.getElementById('entity-list');
        if (!container) return;

        // Filter out any invalid entities before rendering
        const validEntities = this.entities.filter(entity => {
            const isValid = entity && entity.id && entity.name;
            if (!isValid) {
                console.warn('⚠️ Filtering out invalid entity:', entity);
            }
            return isValid;
        });

        if (validEntities.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No entities found</h3>
                    <p>Create your first character, location, or artifact to get started.</p>
                    <button onclick="window.entityManager.showCreateModal()" class="primary-btn">
                        + Create Entity
                    </button>
                </div>
            `;
            return;
        }

        const html = validEntities.map(entity => this.renderEntityCard(entity)).join('');
        container.innerHTML = html;
    }

    renderEntityCard(entity) {
        // Validate entity has required fields
        if (!entity || !entity.id || !entity.name) {
            console.error('❌ Invalid entity structure for card rendering:', entity);
            return ''; // Return empty string instead of broken HTML
        }
        
        const description = (entity.description || '').substring(0, 150) + 
                          (entity.description && entity.description.length > 150 ? '...' : '');
        
        const entityType = entity.entity_type || 'unknown';
        
        return `
            <div class="entity-card" data-id="${entity.id}">
                <div class="entity-card-header">
                    <h3 class="entity-name">${this.escapeHtml(entity.name)}</h3>
                    <span class="entity-type ${entityType}">${entityType}</span>
                </div>
                
                <p class="entity-description">${this.escapeHtml(description)}</p>
                
                <div class="entity-actions">
                    <button class="action-btn edit" onclick="window.entityManager.showEditModal('${entity.id}')">
                        Edit
                    </button>
                    <button class="action-btn delete" onclick="window.entityManager.showDeleteModal('${entity.id}')">
                        Delete
                    </button>
                </div>
            </div>
        `;
    }

    showLoadingState() {
        const container = document.getElementById('entity-list');
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <p>Loading entities...</p>
                </div>
            `;
        }
    }

    updatePagination() {
        const pagination = document.getElementById('pagination');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');

        if (this.totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        
        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= this.totalPages;
        if (pageInfo) pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
    }
    
    updateEntityCount() {
        const countElement = document.getElementById('entity-count');
        if (countElement) {
            const count = this.entities.length;
            countElement.textContent = `${count} ${count === 1 ? 'entity' : 'entities'}`;
        }
    }

    // =================================================================
    // MODAL MANAGEMENT
    // =================================================================

    showCreateModal() {
        this.editingEntity = null;
        document.getElementById('modal-title').textContent = 'Create Entity';
        
        // Clear form
        document.getElementById('entity-name').value = '';
        document.getElementById('entity-type').value = '';
        document.getElementById('entity-description').value = '';
        
        this.showModal();
    }

    showEditModal(entityId) {
        const entity = this.entities.find(e => e.id === entityId);
        if (!entity) return;

        this.editingEntity = entity;
        document.getElementById('modal-title').textContent = 'Edit Entity';
        
        // Populate form
        document.getElementById('entity-name').value = entity.name || '';
        document.getElementById('entity-type').value = entity.entity_type || '';
        document.getElementById('entity-description').value = entity.description || '';
        
        this.showModal();
    }

    showModal() {
        document.getElementById('entity-modal').style.display = 'flex';
        document.getElementById('entity-name').focus();
    }

    hideModal() {
        document.getElementById('entity-modal').style.display = 'none';
        this.editingEntity = null;
    }

    showDeleteModal(entityId) {
        const entity = this.entities.find(e => e.id === entityId);
        if (!entity) return;

        this.entityToDelete = entity;
        document.getElementById('delete-entity-name').textContent = entity.name;
        document.getElementById('delete-modal').style.display = 'flex';
    }

    hideDeleteModal() {
        document.getElementById('delete-modal').style.display = 'none';
        this.entityToDelete = null;
    }

    // =================================================================
    // EVENT HANDLERS
    // =================================================================

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const entityData = {
            name: document.getElementById('entity-name').value.trim(),
            entity_type: document.getElementById('entity-type').value,
            description: document.getElementById('entity-description').value.trim()
        };

        // Validation
        if (!entityData.name) {
            this.showError('Name is required');
            return;
        }
        
        if (!entityData.entity_type) {
            this.showError('Type is required');
            return;
        }

        // Create or update
        if (this.editingEntity) {
            await this.updateEntity(this.editingEntity.id, entityData);
        } else {
            await this.createEntity(entityData);
        }
    }

    async confirmDelete() {
        if (this.entityToDelete) {
            await this.deleteEntity(this.entityToDelete.id);
        }
    }

    handleFilterChange(filterType, value) {
        this.filters[filterType] = value;
        this.currentPage = 1; // Reset to first page
        this.loadEntities();
    }

    clearFilters() {
        this.filters = { type: '', search: '' };
        this.currentPage = 1;
        
        document.getElementById('type-filter').value = '';
        document.getElementById('search-input').value = '';
        
        this.loadEntities();
    }

    changePage(newPage) {
        if (newPage < 1 || newPage > this.totalPages) return;
        
        this.currentPage = newPage;
        this.loadEntities();
    }

    // =================================================================
    // UTILITY METHODS
    // =================================================================

    showSuccess(message) {
        console.log('✅ Success:', message);
        // TODO: Add toast notification
    }

    showError(message) {
        console.error('❌ Error:', message);
        alert('Error: ' + message); // Simple for now
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('entity-manager')) {
        window.entityManager = new EntityManager();
    }
});