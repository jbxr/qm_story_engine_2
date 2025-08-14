/**
 * Dynamic Page Loader for QuantumMateria Story Engine
 * Handles loading separate HTML pages into main content area
 */

class PageLoader {
    constructor() {
        this.currentPage = null;
        this.pageCache = new Map(); // Cache loaded pages for better performance
        this.mainContent = null;
        this.init();
    }

    init() {
        // Get main content container
        this.mainContent = document.getElementById('main-content');
        if (!this.mainContent) {
            console.error('❌ PageLoader: main-content element not found');
            return;
        }
        
        // Load default page (welcome) on initialization
        this.loadPage('welcome');
        
        console.log('✅ PageLoader initialized successfully');
    }

    async loadPage(pageName) {
        try {
            console.log(`🔄 Loading page: ${pageName}`);
            
            // Show loading state
            this.showLoadingState();
            
            // Update navigation active state immediately for responsive feel
            this.updateNavigationState(pageName);
            
            // Get page content (from cache or fetch)
            const content = await this.getPageContent(pageName);
            
            // Insert content into main area
            this.mainContent.innerHTML = content;
            
            // Run page-specific initialization
            this.initializePage(pageName);
            
            // Update current page tracking
            this.currentPage = pageName;
            
            console.log(`✅ Page loaded successfully: ${pageName}`);
            
        } catch (error) {
            console.error(`❌ Failed to load page ${pageName}:`, error);
            this.showErrorState(error.message);
        }
    }

    async getPageContent(pageName) {
        // Check cache first
        if (this.pageCache.has(pageName)) {
            console.log(`📦 Loading ${pageName} from cache`);
            return this.pageCache.get(pageName);
        }
        
        // Fetch from server
        const response = await fetch(`/static/pages/${pageName}.html`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch page: ${response.status} ${response.statusText}`);
        }
        
        const content = await response.text();
        
        // Cache the content for future use
        this.pageCache.set(pageName, content);
        
        console.log(`📥 Fetched and cached ${pageName} page`);
        return content;
    }

    showLoadingState() {
        this.mainContent.innerHTML = `
            <section>
                <div style="text-align: center; padding: 2rem;">
                    <span aria-busy="true">Loading page...</span>
                </div>
            </section>
        `;
    }

    showErrorState(message) {
        this.mainContent.innerHTML = `
            <section>
                <article>
                    <header>
                        <h2>Page Load Error</h2>
                    </header>
                    <p>Failed to load the requested page: ${this.escapeHtml(message)}</p>
                    <footer>
                        <button onclick="window.pageLoader?.loadPage('welcome')">
                            Return to Dashboard
                        </button>
                    </footer>
                </article>
            </section>
        `;
    }

    updateNavigationState(pageName) {
        // Remove active state from all nav links
        document.querySelectorAll('aside nav a').forEach(link => {
            link.removeAttribute('aria-current');
        });
        
        // Map page names to navigation indices
        const pageToNavIndex = {
            'welcome': 0,
            'scenes': 1,
            'entities': 2,
            'scene-editor': 1 // Scene editor should highlight "Scenes" nav
        };
        
        const navIndex = pageToNavIndex[pageName] ?? 0;
        const navLinks = document.querySelectorAll('aside nav a');
        
        if (navLinks[navIndex]) {
            navLinks[navIndex].setAttribute('aria-current', 'page');
        }
        
        console.log(`🎯 Navigation updated for page: ${pageName} (nav index: ${navIndex})`);
    }

    initializePage(pageName) {
        // Run page-specific initialization logic
        switch (pageName) {
            case 'welcome':
                this.initializeWelcomePage();
                break;
            case 'scenes':
                this.initializeScenesPage();
                break;
            case 'entities':
                this.initializeEntitiesPage();
                break;
            case 'scene-editor':
                this.initializeSceneEditorPage();
                break;
            default:
                console.log(`No specific initialization for page: ${pageName}`);
        }
    }

    initializeWelcomePage() {
        // Re-attach event listeners for demo buttons
        const demoSupabaseBtn = document.getElementById('demo-supabase');
        const demoFastApiBtn = document.getElementById('demo-fastapi');
        
        if (demoSupabaseBtn && window.storyEngine) {
            demoSupabaseBtn.addEventListener('click', () => window.storyEngine.demoSupabaseDirect());
        }
        
        if (demoFastApiBtn && window.storyEngine) {
            demoFastApiBtn.addEventListener('click', () => window.storyEngine.demoFastApiCommand());
        }
        
        console.log('🏠 Welcome page initialized');
    }

    initializeScenesPage() {
        // Re-attach event listeners and load scenes data
        const createSceneBtn = document.getElementById('create-scene-btn');
        
        if (createSceneBtn && window.storyEngine) {
            createSceneBtn.addEventListener('click', () => window.storyEngine.createScene());
        }
        
        // Load scenes data if storyEngine is available
        if (window.storyEngine) {
            // Small delay to ensure DOM is fully ready
            setTimeout(() => {
                window.storyEngine.loadScenes();
                window.storyEngine.updateScenesCount();
            }, 50);
        }
        
        console.log('🎬 Scenes page initialized');
    }

    initializeEntitiesPage() {
        // Initialize or reinitialize entity manager for this page
        if (window.EntityManager) {
            // Create a new entity manager instance for this page
            window.entityManager = new EntityManager();
        } else {
            console.warn('⚠️ EntityManager class not available, falling back to basic functionality');
            
            // Fallback: use basic entity functionality from StoryEngine
            const createEntityBtn = document.getElementById('create-entity-btn');
            if (createEntityBtn && window.storyEngine) {
                createEntityBtn.addEventListener('click', () => window.storyEngine.createEntity());
            }
        }
        
        console.log('👥 Entities page initialized');
    }

    initializeSceneEditorPage() {
        // Scene editor specific initialization
        // Event listeners for scene editing controls
        const addProseBtn = document.getElementById('add-prose');
        const addDialogueBtn = document.getElementById('add-dialogue');
        const addMilestoneBtn = document.getElementById('add-milestone');
        
        // These would need to be implemented in the StoryEngine class
        if (addProseBtn && window.storyEngine) {
            // addProseBtn.addEventListener('click', () => window.storyEngine.addProseBlock());
        }
        
        console.log('✏️ Scene editor page initialized');
    }

    // Navigation helper methods for backward compatibility
    showView(viewName) {
        // Map old view names to new page names
        const viewToPageMap = {
            'welcome-state': 'welcome',
            'scenes-list': 'scenes',
            'entity-manager': 'entities',
            'scene-editor': 'scene-editor'
        };
        
        const pageName = viewToPageMap[viewName] || viewName;
        this.loadPage(pageName);
    }

    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

}

// Initialize the page loader when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pageLoader = new PageLoader();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PageLoader;
}