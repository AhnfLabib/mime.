class CreepypastaScraper {
    constructor() {
        this.isScraping = false;
        this.stories = [];
        this.genres = {};
        this.currentGenre = 'all';
        this.pollInterval = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadExistingData();
    }

    initializeElements() {
        this.startBtn = document.getElementById('startBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.progressPercent = document.getElementById('progressPercent');
        this.statsDashboard = document.getElementById('statsDashboard');
        this.totalStories = document.getElementById('totalStories');
        this.totalGenres = document.getElementById('totalGenres');
        this.scrapingTime = document.getElementById('scrapingTime');
        this.genreFilter = document.getElementById('genreFilter');
        this.genreButtons = document.getElementById('genreButtons');
        this.storiesSection = document.getElementById('storiesSection');
        this.storiesGrid = document.getElementById('storiesGrid');
        this.storyModal = document.getElementById('storyModal');
        this.closeModal = document.getElementById('closeModal');

        // Generate UI
        this.generateSection = document.getElementById('generateSection');
        this.genGenre = document.getElementById('genGenre');
        this.genTropes = document.getElementById('genTropes');
        this.genWordCount = document.getElementById('genWordCount');
        this.genSeeds = document.getElementById('genSeeds');
        this.genBtn = document.getElementById('genBtn');
        this.genResult = document.getElementById('genResult');
        this.genStory = document.getElementById('genStory');

        // Always allow generation UI to be visible
        if (this.generateSection) {
            this.generateSection.style.display = 'block';
        }
    }

    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startScraping());
        this.closeModal.addEventListener('click', () => this.closeStoryModal());
        this.storyModal.addEventListener('click', (e) => {
            if (e.target === this.storyModal) {
                this.closeStoryModal();
            }
        });

        if (this.genBtn) {
            this.genBtn.addEventListener('click', () => this.generateStory());
        }
    }

    async loadExistingData() {
        try {
            const response = await fetch('/api/stories');
            if (response.ok) {
                const data = await response.json();
                if (data.stories && data.stories.length > 0) {
                    this.stories = data.stories;
                    this.genres = data.genres;
                    this.updateUI();
                }
            }
        } catch (error) {
            console.error('Error loading existing data:', error);
        }
    }

    async startScraping() {
        if (this.isScraping) return;

        try {
            this.isScraping = true;
            this.startBtn.disabled = true;
            this.startBtn.innerHTML = '<span class="loading"></span> Starting...';
            
            const response = await fetch('/api/start-scraping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.showProgress();
                this.startPolling();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to start scraping');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    showProgress() {
        this.progressContainer.style.display = 'block';
        this.statusIndicator.querySelector('.status-dot').classList.add('running');
        this.statusText.textContent = 'Scraping...';
    }

    startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                this.updateProgress(status);
                
                if (!status.is_running) {
                    this.stopPolling();
                    if (status.error) {
                        this.showError(status.error);
                    } else {
                        this.loadStories();
                    }
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 2000);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.isScraping = false;
        this.startBtn.disabled = false;
        this.startBtn.innerHTML = '<span class="btn-icon">🕷️</span> Start Scraping';
    }

    updateProgress(status) {
        const progress = Math.round(status.progress || 0);
        this.progressFill.style.width = progress + '%';
        this.progressText.textContent = `${status.current_item || 0} / ${status.total_items || 50} stories`;
        this.progressPercent.textContent = progress + '%';

        if (status.start_time) {
            const startTime = new Date(status.start_time);
            const now = new Date();
            const elapsed = Math.round((now - startTime) / 1000);
            this.scrapingTime.textContent = elapsed + 's';
        }
    }

    async loadStories() {
        try {
            const response = await fetch('/api/stories');
            const data = await response.json();
            
            this.stories = data.stories;
            this.genres = data.genres;
            this.updateUI();
            
            // Hide progress and show completion
            this.progressContainer.style.display = 'none';
            this.statusIndicator.querySelector('.status-dot').classList.remove('running');
            this.statusIndicator.querySelector('.status-dot').classList.add('completed');
            this.statusText.textContent = 'Completed';
            
        } catch (error) {
            this.showError('Error loading stories: ' + error.message);
        }
    }

    updateUI() {
        this.updateStats();
        this.updateGenreFilter();
        this.updateStoriesGrid();
    }

    updateStats() {
        this.totalStories.textContent = this.stories.length;
        this.totalGenres.textContent = Object.keys(this.genres).length;
        
        if (this.stories.length > 0) {
            this.statsDashboard.style.display = 'grid';
            this.genreFilter.style.display = 'block';
            this.storiesSection.style.display = 'block';
            if (this.generateSection) this.generateSection.style.display = 'block';
            this.populateGenerateGenres();
        }
    }

    populateGenerateGenres() {
        if (!this.genGenre) return;
        const current = this.genGenre.value;
        this.genGenre.innerHTML = '';
        let genres = Object.keys(this.genres);
        if (genres.length === 0) {
            genres = ['Psychological', 'Supernatural', 'Sci-Fi', 'Creature', 'Crime', 'Urban Legend'];
        }
        genres.forEach((g, idx) => {
            const opt = document.createElement('option');
            opt.value = g; opt.textContent = g;
            if (idx === 0) opt.selected = true;
            this.genGenre.appendChild(opt);
        });
        if (current) this.genGenre.value = current;
    }

    async generateStory() {
        try {
            this.genBtn.disabled = true;
            this.genBtn.textContent = 'Generating...';
            this.genResult.style.display = 'none';
            this.genStory.textContent = '';

            const genre = this.genGenre && this.genGenre.value ? this.genGenre.value : 'Psychological';
            const tropes = (this.genTropes && this.genTropes.value ? this.genTropes.value : '')
                .split(',')
                .map(t => t.trim())
                .filter(Boolean);
            const wordCount = parseInt(this.genWordCount && this.genWordCount.value ? this.genWordCount.value : '900', 10) || 900;
            const seedTitles = parseInt(this.genSeeds && this.genSeeds.value ? this.genSeeds.value : '2', 10) || 2;

            const resp = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    genre,
                    tropes,
                    style: { word_count: wordCount },
                    seed_titles: seedTitles
                })
            });

            const data = await resp.json();
            if (!resp.ok) {
                throw new Error(data.error || 'Generation failed');
            }
            this.genStory.textContent = data.story || 'No content generated';
            this.genResult.style.display = 'block';
        } catch (e) {
            this.genStory.textContent = 'Error: ' + e.message;
            this.genResult.style.display = 'block';
        } finally {
            this.genBtn.disabled = false;
            this.genBtn.textContent = 'Generate Story';
        }
    }

    updateGenreFilter() {
        this.genreButtons.innerHTML = '';
        
        // Add "All" button
        const allBtn = document.createElement('button');
        allBtn.className = `genre-btn ${this.currentGenre === 'all' ? 'active' : ''}`;
        allBtn.textContent = `All (${this.stories.length})`;
        allBtn.addEventListener('click', () => this.filterByGenre('all'));
        this.genreButtons.appendChild(allBtn);
        
        // Add genre buttons
        Object.entries(this.genres).forEach(([genre, count]) => {
            const btn = document.createElement('button');
            btn.className = `genre-btn ${this.currentGenre === genre ? 'active' : ''}`;
            btn.textContent = `${genre} (${count})`;
            btn.addEventListener('click', () => this.filterByGenre(genre));
            this.genreButtons.appendChild(btn);
        });
    }

    filterByGenre(genre) {
        this.currentGenre = genre;
        this.updateGenreFilter();
        this.updateStoriesGrid();
    }

    updateStoriesGrid() {
        this.storiesGrid.innerHTML = '';
        
        const filteredStories = this.currentGenre === 'all' 
            ? this.stories 
            : this.stories.filter(story => (story.genre_primary || story.genre) === this.currentGenre);
        
        filteredStories.forEach(story => {
            const storyCard = this.createStoryCard(story);
            this.storiesGrid.appendChild(storyCard);
        });
    }

    createStoryCard(story) {
        const card = document.createElement('div');
        card.className = 'story-card';
        card.addEventListener('click', () => this.showStoryModal(story));
        
        const preview = story.content ? story.content.substring(0, 150) + '...' : 'No content available';
        
        card.innerHTML = `
            <div class="story-title">${story.title || 'Untitled'}</div>
            <div class="story-author">by ${story.author || 'Unknown'}</div>
            <div class="story-genre">${(story.genre_primary || story.genre) || 'Uncategorized'}</div>
            <div class="story-preview">${preview}</div>
            <div class="story-tags">
                ${(story.tags || []).map(tag => `<span class="story-tag">${tag}</span>`).join('')}
            </div>
        `;
        
        return card;
    }

    showStoryModal(story) {
        document.getElementById('modalTitle').textContent = story.title || 'Untitled';
        document.getElementById('modalAuthor').textContent = story.author || 'Unknown';
        document.getElementById('modalGenre').textContent = (story.genre_primary || story.genre) || 'Uncategorized';
        document.getElementById('modalDate').textContent = story.publication_date || 'Unknown date';
        document.getElementById('modalContent').textContent = story.content || 'No content available';
        
        const tagsContainer = document.getElementById('modalTags');
        tagsContainer.innerHTML = '';
        if (story.tags && story.tags.length > 0) {
            story.tags.forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'story-tag';
                tagEl.textContent = tag;
                tagsContainer.appendChild(tagEl);
            });
        }
        
        this.storyModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    closeStoryModal() {
        this.storyModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    showError(message) {
        this.statusText.textContent = 'Error: ' + message;
        this.statusIndicator.querySelector('.status-dot').classList.remove('running');
        this.statusIndicator.querySelector('.status-dot').style.background = '#ff0000';
        this.stopPolling();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CreepypastaScraper();
});

