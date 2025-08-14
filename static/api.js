/**
 * Simple API wrapper for FastAPI integration
 * Handles common patterns for the QuantumMateria Story Engine
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseUrl}${endpoint}`;
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                },
                ...options
            };

            if (config.body && typeof config.body === 'object') {
                config.body = JSON.stringify(config.body);
            }

            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `API request failed: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API request failed [${endpoint}]:`, error);
            throw error;
        }
    }

    // GET requests
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST requests
    async post(endpoint, data) {
        return this.request(endpoint, { 
            method: 'POST', 
            body: data 
        });
    }

    // PUT requests
    async put(endpoint, data) {
        return this.request(endpoint, { 
            method: 'PUT', 
            body: data 
        });
    }

    // DELETE requests
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // =================================================================
    // SCENE OPERATIONS
    // =================================================================

    async getScene(sceneId) {
        return this.get(`/api/scenes/${sceneId}`);
    }

    async getSceneBlocks(sceneId) {
        return this.get(`/api/v1/scenes/${sceneId}/blocks`);
    }

    async getSceneEntities(sceneId) {
        // For now, return empty entities since this endpoint might not exist yet
        return { success: true, data: { entities: [] } };
    }

    async createSceneBlock(sceneId, blockData) {
        return this.post(`/api/scenes/${sceneId}/blocks`, blockData);
    }

    async updateSceneBlock(sceneId, blockId, blockData) {
        return this.put(`/api/scenes/${sceneId}/blocks/${blockId}`, blockData);
    }

    async deleteSceneBlock(sceneId, blockId) {
        return this.delete(`/api/scenes/${sceneId}/blocks/${blockId}`);
    }

    async reorderSceneBlocks(sceneId, blockIds) {
        return this.put(`/api/scenes/${sceneId}/blocks/reorder`, { block_ids: blockIds });
    }

    // =================================================================
    // ENTITY OPERATIONS
    // =================================================================

    async getEntities(entityType = null) {
        const endpoint = entityType ? `/api/entities?entity_type=${entityType}` : '/api/entities';
        return this.get(endpoint);
    }

    async getEntity(entityId) {
        return this.get(`/api/entities/${entityId}`);
    }

    // =================================================================
    // SYSTEM OPERATIONS
    // =================================================================

    async getHealth() {
        return this.get('/health');
    }

    async getConfig() {
        return this.get('/api/config');
    }
}

// Export for use in other scripts
window.ApiClient = ApiClient;