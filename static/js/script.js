/*
News Summary Bot - JavaScript Logic
Developer: Molla Samser
Design & Testing: Rima Khatun
Company: RSK World
Year: 2026
Website: https://rskworld.in
*/

let currentCategory = 'general';
let lastContent = ''; // For regeneration

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('news-grid')) {
        loadCategory('general');
        updateTrends();
    }
});

function loadCategory(category) {
    currentCategory = category;

    // Update UI
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(category)) {
            item.classList.add('active');
        }
    });

    fetchNews(`/api/news?category=${category}`);
}

function searchNews() {
    const query = document.getElementById('newsQuery').value;
    if (query.trim()) {
        fetchNews(`/api/news?q=${encodeURIComponent(query)}`);
    }
}

async function fetchNews(url) {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = `
        <div class="glass-card" style="grid-column: 1/-1; text-align: center;">
            <span class="loader"></span>
            <p>Fetching latest news headlines...</p>
        </div>
    `;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            grid.innerHTML = `<div class="glass-card" style="grid-column: 1/-1; color: #ff4444;">Error: ${data.error}</div>`;
            return;
        }

        const articles = data.articles;
        if (!articles || articles.length === 0) {
            grid.innerHTML = `<div class="glass-card" style="grid-column: 1/-1;">No news articles found.</div>`;
            return;
        }

        grid.innerHTML = articles.map((article, index) => {
            const encodedContent = encodeURIComponent(article.description || article.title);
            return `
            <div class="news-card glass-card">
                <img src="${article.urlToImage || 'https://via.placeholder.com/300x200?text=News+Article'}" alt="News" class="news-image" onerror="this.src='https://via.placeholder.com/300x200?text=News+Article'">
                <div id="sentiment-${index}" class="badge-sentiment bg-neutral">Analyzing...</div>
                <h4>${article.title}</h4>
                <p style="font-size: 0.9rem; color: #888; margin: 0.5rem 0;">${article.source.name} • ${new Date(article.publishedAt).toLocaleDateString()}</p>
                <div style="margin-top: 1rem; display: flex; gap: 10px;">
                    <button onclick="showSummary('${index}', '${encodedContent}')" class="btn-premium" style="padding: 0.4rem 1rem; font-size: 0.8rem;">Summarize</button>
                    <a href="${article.url}" target="_blank" class="btn-premium" style="padding: 0.4rem 1rem; font-size: 0.8rem; background: var(--glass);">Read More</a>
                </div>
            </div>
            `;
        }).join('');

        // Trigger sentiment analysis for each card
        articles.forEach((article, index) => {
            updateSentiment(index, article.title);
        });

    } catch (err) {
        grid.innerHTML = `<div class="glass-card" style="grid-column: 1/-1; color: #ff4444;">Failed to fetch news. Please check your connection.</div>`;
    }
}

async function updateSentiment(index, text) {
    const badge = document.getElementById(`sentiment-${index}`);
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
        const data = await response.json();
        const sentiment = data.sentiment || 'Neutral';

        badge.innerText = sentiment;
        badge.className = `badge-sentiment bg-${sentiment.toLowerCase()}`;
    } catch {
        badge.innerText = 'Neutral';
    }
}

async function showSummary(index, content) {
    lastContent = decodeURIComponent(content);
    const modal = document.getElementById('summaryModal');
    const summaryText = document.getElementById('summary-text');

    modal.style.display = 'flex';
    requestSummary();
}

async function requestSummary() {
    const summaryText = document.getElementById('summary-text');
    const language = document.getElementById('summaryLanguage').value;
    summaryText.innerHTML = '<span class="loader"></span> Generating AI Summary...';

    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: lastContent, language: language })
        });
        const data = await response.json();

        if (data.summary) {
            summaryText.innerText = data.summary;
        } else {
            summaryText.innerText = data.error || "Could not generate summary.";
        }
    } catch (err) {
        summaryText.innerText = "Error connecting to summarization service.";
    }
}

function regenerateSummary() {
    requestSummary();
}

function speakSummary() {
    const text = document.getElementById('summary-text').innerText;
    if ('speechSynthesis' in window) {
        // Cancel existing speech
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const language = document.getElementById('summaryLanguage').value;

        // Basic mapping for major languages
        const langMap = {
            'English': 'en-US',
            'Hindi': 'hi-IN',
            'Spanish': 'es-ES',
            'French': 'fr-FR',
            'German': 'de-DE'
        };
        utterance.lang = langMap[language] || 'en-US';
        window.speechSynthesis.speak(utterance);
    } else {
        alert("Sorry, your browser doesn't support text to speech!");
    }
}

async function updateTrends() {
    const container = document.getElementById('trending-topics');
    if (!container) return;
    
    try {
        const response = await fetch('/api/trending?days=7');
        const data = await response.json();
        
        if (data.trending && data.trending.length > 0) {
            const topics = data.trending.slice(0, 7).flatMap(t => t.keywords || []).slice(0, 7);
            container.innerHTML = topics.map(topic => 
                `<span class="trend-tag" onclick="document.getElementById('newsQuery').value='${topic}'; searchNews();">${topic}</span>`
            ).join('');
        } else {
            // Fallback to default trends
            const trends = ['AI Chatbots', 'Global Economy', 'SpaceX', 'Web3', 'Blockchain', 'Sustainability', 'Tech Jobs'];
            container.innerHTML = trends.map(t => 
                `<span class="trend-tag" onclick="document.getElementById('newsQuery').value='${t}'; searchNews();">${t}</span>`
            ).join('');
        }
    } catch (error) {
        console.error('Error fetching trends:', error);
        // Fallback to default trends
        const trends = ['AI Chatbots', 'Global Economy', 'SpaceX', 'Web3', 'Blockchain', 'Sustainability', 'Tech Jobs'];
        container.innerHTML = trends.map(t => 
            `<span class="trend-tag" onclick="document.getElementById('newsQuery').value='${t}'; searchNews();">${t}</span>`
        ).join('');
    }
}

function closeModal() {
    window.speechSynthesis.cancel();
    document.getElementById('summaryModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('summaryModal');
    if (event.target == modal) {
        closeModal();
    }
}

// Voice Search Implementation
let recognition = null;
let isListening = false;

function initVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('newsQuery').value = transcript;
            searchNews();
            toggleVoiceSearch(); // Stop listening
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            alert('Voice recognition error. Please try again.');
            toggleVoiceSearch(); // Stop listening
        };

        recognition.onend = function() {
            if (isListening) {
                const btn = document.getElementById('voiceSearchBtn');
                if (btn) {
                    btn.classList.remove('listening');
                    isListening = false;
                }
            }
        };
    }
}

function toggleVoiceSearch() {
    if (!recognition) {
        initVoiceRecognition();
    }

    if (!recognition) {
        alert('Your browser does not support voice recognition. Please use Chrome or Edge.');
        return;
    }

    const btn = document.getElementById('voiceSearchBtn');
    
    if (isListening) {
        recognition.stop();
        btn.classList.remove('listening');
        isListening = false;
    } else {
        recognition.start();
        btn.classList.add('listening');
        isListening = true;
    }
}

// Initialize voice recognition on page load
document.addEventListener('DOMContentLoaded', () => {
    initVoiceRecognition();
});

// PDF Export Implementation
function exportSummaryPDF() {
    const title = document.getElementById('modal-title').innerText;
    const summary = document.getElementById('summary-text').innerText;
    const language = document.getElementById('summaryLanguage').value;
    
    if (!summary || summary.includes('Generating') || summary.includes('Error')) {
        alert('Please wait for the summary to be generated.');
        return;
    }

    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Add title
        doc.setFontSize(18);
        doc.text(title, 20, 20);
        
        // Add language info
        doc.setFontSize(12);
        doc.text(`Language: ${language}`, 20, 30);
        doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 37);
        
        // Add summary text with word wrap
        doc.setFontSize(11);
        const lines = doc.splitTextToSize(summary, 170);
        doc.text(lines, 20, 50);
        
        // Add footer
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setFontSize(8);
            doc.text(`Page ${i} of ${pageCount} | RSK World News Bot`, 20, doc.internal.pageSize.height - 10);
        }
        
        // Save the PDF
        doc.save(`news-summary-${Date.now()}.pdf`);
    } catch (error) {
        console.error('PDF export error:', error);
        alert('Error generating PDF. Please make sure jsPDF library is loaded.');
    }
}

// Bookmarks/Favorites System
let bookmarks = JSON.parse(localStorage.getItem('newsBookmarks') || '[]');

function toggleBookmark(articleIndex, article) {
    const bookmarkKey = `bookmark_${article.url || article.title}`;
    const existingIndex = bookmarks.findIndex(b => b.url === article.url);
    
    if (existingIndex >= 0) {
        // Remove bookmark
        bookmarks.splice(existingIndex, 1);
        updateBookmarkButton(articleIndex, false);
    } else {
        // Add bookmark
        bookmarks.push({
            title: article.title,
            url: article.url,
            description: article.description,
            source: article.source?.name,
            publishedAt: article.publishedAt,
            urlToImage: article.urlToImage,
            savedAt: new Date().toISOString()
        });
        updateBookmarkButton(articleIndex, true);
    }
    
    localStorage.setItem('newsBookmarks', JSON.stringify(bookmarks));
}

function updateBookmarkButton(index, isBookmarked) {
    const card = document.querySelectorAll('.news-card')[index];
    if (card) {
        let btn = card.querySelector('.bookmark-btn');
        if (!btn) {
            // Create bookmark button if it doesn't exist
            const btnContainer = card.querySelector('div[style*="margin-top: 1rem"]');
            if (btnContainer) {
                btn = document.createElement('button');
                btn.className = 'bookmark-btn';
                btn.innerHTML = '<i class="fas fa-bookmark"></i>';
                btn.onclick = () => {
                    const articles = JSON.parse(sessionStorage.getItem('currentArticles') || '[]');
                    if (articles[index]) {
                        toggleBookmark(index, articles[index]);
                    }
                };
                btnContainer.insertBefore(btn, btnContainer.firstChild);
            }
        }
        if (btn) {
            btn.classList.toggle('active', isBookmarked);
        }
    }
}

function loadBookmarks() {
    const grid = document.getElementById('news-grid');
    if (bookmarks.length === 0) {
        grid.innerHTML = '<div class="glass-card" style="grid-column: 1/-1; text-align: center;">No bookmarks saved yet.</div>';
        return;
    }
    
    grid.innerHTML = bookmarks.map((bookmark, index) => {
        return `
        <div class="news-card glass-card">
            <img src="${bookmark.urlToImage || 'https://via.placeholder.com/300x200?text=News+Article'}" alt="News" class="news-image" onerror="this.src='https://via.placeholder.com/300x200?text=News+Article'">
            <div class="badge-sentiment bg-neutral">Bookmarked</div>
            <h4>${bookmark.title}</h4>
            <p style="font-size: 0.9rem; color: #888; margin: 0.5rem 0;">${bookmark.source || 'Unknown'} • ${new Date(bookmark.publishedAt).toLocaleDateString()}</p>
            <p style="font-size: 0.85rem; color: #aaa; margin: 0.5rem 0;">${bookmark.description || ''}</p>
            <div style="margin-top: 1rem; display: flex; gap: 10px;">
                <button onclick="toggleBookmark(${index}, ${JSON.stringify(bookmark).replace(/"/g, '&quot;')})" class="bookmark-btn active"><i class="fas fa-bookmark"></i></button>
                <button onclick="showSummary('${index}', '${encodeURIComponent(bookmark.description || bookmark.title)}')" class="btn-premium" style="padding: 0.4rem 1rem; font-size: 0.8rem;">Summarize</button>
                <a href="${bookmark.url}" target="_blank" class="btn-premium" style="padding: 0.4rem 1rem; font-size: 0.8rem; background: var(--glass);">Read More</a>
            </div>
        </div>
        `;
    }).join('');
}

// Update fetchNews to store articles and add bookmark buttons
const originalFetchNews = fetchNews;
fetchNews = async function(url) {
    const result = await originalFetchNews(url);
    
    // Store articles in sessionStorage for bookmark functionality
    try {
        const response = await fetch(url);
        const data = await response.json();
        if (data.articles) {
            sessionStorage.setItem('currentArticles', JSON.stringify(data.articles));
            
            // Add bookmark buttons to articles
            data.articles.forEach((article, index) => {
                const isBookmarked = bookmarks.some(b => b.url === article.url);
                setTimeout(() => updateBookmarkButton(index, isBookmarked), 100);
            });
        }
    } catch (e) {
        console.error('Error storing articles:', e);
    }
    
    return result;
};

// Update loadCategory to handle bookmarks
const originalLoadCategory = loadCategory;
loadCategory = function(category) {
    if (category === 'bookmarks') {
        loadBookmarks();
        // Update UI
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('onclick') && item.getAttribute('onclick').includes('bookmarks')) {
                item.classList.add('active');
            }
        });
    } else {
        originalLoadCategory(category);
    }
};

// Update trending topics to use API
async function updateTrends() {
    const container = document.getElementById('trending-topics');
    if (!container) return;
    
    try {
        const response = await fetch('/api/trending?days=7');
        const data = await response.json();
        
        if (data.trending && data.trending.length > 0) {
            const topics = data.trending.slice(0, 7).flatMap(t => t.keywords || []);
            container.innerHTML = topics.map(topic => 
                `<span class="trend-tag" onclick="document.getElementById('newsQuery').value='${topic}'; searchNews();">${topic}</span>`
            ).join('');
        } else {
            // Fallback to default trends
            const trends = ['AI Chatbots', 'Global Economy', 'SpaceX', 'Web3', 'Blockchain', 'Sustainability', 'Tech Jobs'];
            container.innerHTML = trends.map(t => 
                `<span class="trend-tag" onclick="document.getElementById('newsQuery').value='${t}'; searchNews();">${t}</span>`
            ).join('');
        }
    } catch (error) {
        console.error('Error fetching trends:', error);
        // Fallback to default trends
        const trends = ['AI Chatbots', 'Global Economy', 'SpaceX', 'Web3', 'Blockchain', 'Sustainability', 'Tech Jobs'];
        container.innerHTML = trends.map(t => 
            `<span class="trend-tag" onclick="document.getElementById('newsQuery').value='${t}'; searchNews();">${t}</span>`
        ).join('');
    }
}

// Developed by Molla Samser | 2026 | RSK World
