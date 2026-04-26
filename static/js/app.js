const API_BASE = (typeof window !== 'undefined' && window.API_BASE) ? window.API_BASE : '';

class MimeConsole {
    constructor() {
        this.stats = null;
        this.isLoading = false;
        this.storyText = '';
        this.initializeElements();
        this.bindEvents();
        this.loadStats();
    }

    initializeElements() {
        this.totalStories = document.getElementById('totalStories');
        this.totalGenres = document.getElementById('totalGenres');
        this.totalAuthors = document.getElementById('totalAuthors');
        this.genreList = document.getElementById('genreList');
        this.authorList = document.getElementById('authorList');
        this.lastUpdated = document.getElementById('lastUpdated');
        this.refreshStatsBtn = document.getElementById('refreshStatsBtn');

        this.genGenre = document.getElementById('genGenre');
        this.genTropes = document.getElementById('genTropes');
        this.genWordCount = document.getElementById('genWordCount');
        this.genSeeds = document.getElementById('genSeeds');
        this.genStyleNotes = document.getElementById('genStyleNotes');
        this.genBtn = document.getElementById('genBtn');
        this.genStatus = document.getElementById('genStatus');
        this.genResult = document.getElementById('genResult');
        this.genStory = document.getElementById('genStory');
        this.copyStoryBtn = document.getElementById('copyStoryBtn');
    }

    bindEvents() {
        if (this.refreshStatsBtn) {
            this.refreshStatsBtn.addEventListener('click', () => this.loadStats(true));
        }

        if (this.genBtn) {
            this.genBtn.addEventListener('click', () => this.generateStory());
        }

        if (this.copyStoryBtn) {
            this.copyStoryBtn.addEventListener('click', () => this.copyStory());
        }
    }

    async loadStats(isManual = false) {
        if (this.isLoading) return;
        this.isLoading = true;
        if (isManual) {
            this.refreshStatsBtn.textContent = 'Refreshing...';
            this.refreshStatsBtn.disabled = true;
        }
        try {
            const resp = await fetch(`${API_BASE}/api/stats`);
            if (!resp.ok) throw new Error('Failed to load stats');
            const data = await resp.json();
            this.stats = data;
            this.renderStats();
        } catch (err) {
            console.error(err);
            this.genreList.innerHTML = `<p class="empty">Unable to load stats.</p>`;
        } finally {
            this.isLoading = false;
            if (isManual) {
                this.refreshStatsBtn.textContent = 'Refresh';
                this.refreshStatsBtn.disabled = false;
            }
        }
    }

    renderStats() {
        if (!this.stats) return;

        this.totalStories.textContent = this.stats.total_stories?.toLocaleString() || '0';
        const genres = Object.entries(this.stats.genre_distribution || {});
        this.totalGenres.textContent = genres.length.toString();
        if (this.totalAuthors) {
            this.totalAuthors.textContent = this.stats.total_authors?.toLocaleString() || '0';
        }

        if (this.stats.last_updated) {
            const dt = new Date(this.stats.last_updated);
            this.lastUpdated.textContent = dt.toLocaleString();
        }

        this.renderGenreList(genres);
        this.renderAuthorList(this.stats.top_authors || []);
        this.populateGenerateGenres(genres.map(([name]) => name));
    }

    renderGenreList(entries) {
        if (!entries || entries.length === 0) {
            this.genreList.innerHTML = `<p class="empty">No genre data yet.</p>`;
            return;
        }
        const sorted = entries.sort((a, b) => b[1] - a[1]).slice(0, 6);
        const total = this.stats.total_stories || 1;
        this.genreList.innerHTML = '';
        sorted.forEach(([genre, count]) => {
            const pct = Math.round((count / total) * 100);
            const row = document.createElement('div');
            row.className = 'list-row';
            row.innerHTML = `
                <strong>${genre || 'Unclassified'}</strong>
                <span>${count.toLocaleString()} · ${pct}%</span>
            `;
            this.genreList.appendChild(row);
        });
    }

    renderAuthorList(authors) {
        if (!authors || authors.length === 0) {
            this.authorList.innerHTML = `<p class="empty">No author signals yet.</p>`;
            return;
        }
        this.authorList.innerHTML = '';
        authors.forEach((entry) => {
            const row = document.createElement('div');
            row.className = 'list-row';
            row.innerHTML = `
                <strong>${entry.author || 'Unknown'}</strong>
                <span>${entry.count} stories</span>
            `;
            this.authorList.appendChild(row);
        });
    }

    populateGenerateGenres(genreNames) {
        if (!this.genGenre) return;
        this.genGenre.innerHTML = '';
        const fallback = ['Psychological', 'Supernatural', 'Sci-Fi', 'Creature', 'Crime', 'Urban Legend'];
        const options = genreNames && genreNames.length ? genreNames : fallback;
        options.forEach((name, idx) => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            if (idx === 0) opt.selected = true;
            this.genGenre.appendChild(opt);
        });
    }

    async generateStory() {
        if (!this.genBtn) return;
        const genre = this.genGenre?.value || 'Psychological';
        const tropes = (this.genTropes?.value || '')
            .split(',')
            .map(t => t.trim())
            .filter(Boolean);
        const wordCount = parseInt(this.genWordCount?.value || '900', 10) || 900;
        const seedTitles = parseInt(this.genSeeds?.value || '2', 10) || 2;
        const styleNotes = this.genStyleNotes?.value?.trim() || '';

        this.genBtn.disabled = true;
        this.genStatus.textContent = 'Generating via Gemini...';
        this.genStory.textContent = '';
        this.genResult.style.display = 'none';

        try {
            const resp = await fetch(`${API_BASE}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    genre,
                    tropes,
                    style: { word_count: wordCount, notes: styleNotes },
                    seed_titles: seedTitles
                })
            });
            const data = await resp.json();
            if (!resp.ok) {
                throw new Error(data.error || 'Generation failed');
            }
            this.storyText = data.story || '';
            this.genStory.textContent = this.storyText || 'Gemini returned no text.';
            this.genResult.style.display = 'block';
            this.genStatus.textContent = `Generated with ${data.used_seeds?.length || 0} seed references.`;
        } catch (error) {
            this.storyText = '';
            this.genResult.style.display = 'block';
            this.genStory.textContent = `Error: ${error.message}`;
            this.genStatus.textContent = 'Generation failed.';
        } finally {
            this.genBtn.disabled = false;
        }
    }

    async copyStory() {
        if (!this.storyText) return;
        try {
            await navigator.clipboard.writeText(this.storyText);
            this.genStatus.textContent = 'Copied to clipboard.';
            setTimeout(() => {
                this.genStatus.textContent = '';
            }, 2000);
        } catch (err) {
            this.genStatus.textContent = 'Copy failed. Select text manually.';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MimeConsole();
});

