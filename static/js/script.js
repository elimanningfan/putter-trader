document.addEventListener('DOMContentLoaded', function() {
    const putterForm = document.getElementById('putterForm');
    const putterNameInput = document.getElementById('putterName');
    const submitBtn = document.getElementById('submitBtn');
    const loadingDiv = document.getElementById('loading');
    const resultContainer = document.getElementById('resultContainer');
    const putterResult = document.getElementById('putterResult');
    const errorContainer = document.getElementById('errorContainer');
    
    putterForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const putterName = putterNameInput.value.trim();
        
        if (!putterName) {
            alert('Please enter a Scotty Cameron putter name');
            return;
        }
        
        // Show loading, hide results and errors
        loadingDiv.classList.remove('d-none');
        resultContainer.classList.add('d-none');
        errorContainer.classList.add('d-none');
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/putter-info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ putter_name: putterName })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'An error occurred');
            }
            
            // Format the response text with enhanced formatting
            const formattedResponse = formatResponseText(data.response);
            
            // Show results
            putterResult.innerHTML = formattedResponse;
            resultContainer.classList.remove('d-none');
            
            // Scroll to the results
            resultContainer.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            console.error('Error:', error);
            errorContainer.textContent = error.message || 'An error occurred while fetching putter information';
            errorContainer.classList.remove('d-none');
        } finally {
            loadingDiv.classList.add('d-none');
            submitBtn.disabled = false;
        }
    });
    
    // Enhanced formatting function with better structure and emphasis on market value
    function formatResponseText(text) {
        if (!text) return '';
        
        // Add section identification
        text = text.replace(/\*\*Current Market Value\*\*/g, '<!-- MARKET_VALUE_SECTION --><div class="market-value-section"><h2 class="market-value-title">Current Market Value</h2>');
        text = text.replace(/\*\*Basic Information\*\*/g, '<div class="section basic-info-section"><h2>Basic Information</h2>');
        text = text.replace(/\*\*Buying Recommendations\*\*/g, '<div class="section buying-section"><h2>Buying Recommendations</h2>');
        text = text.replace(/\*\*Authentication Tips\*\*/g, '<div class="section auth-section"><h2>Authentication Tips</h2>');
        text = text.replace(/\*\*Technical Specifications\*\*/g, '<div class="section specs-section"><h2>Technical Specifications</h2>');
        text = text.replace(/\*\*Collectibility Factors\*\*/g, '<div class="section collect-section"><h2>Collectibility Factors</h2>');
        text = text.replace(/\*\*Comparable Models\*\*/g, '<div class="section compare-section"><h2>Comparable Models</h2>');
        
        // Close any open section divs before the next section starts
        const sectionHeaders = ['Basic Information', 'Current Market Value', 'Buying Recommendations', 
                               'Authentication Tips', 'Technical Specifications', 'Collectibility Factors', 
                               'Comparable Models'];
        
        sectionHeaders.forEach(header => {
            const pattern = new RegExp(`(.*?)(<div class="section|<div class="market-value-section|$)`, 'gs');
            text = text.replace(pattern, '$1</div>$2');
        });
        
        // Remove any empty/duplicated closing div tags
        text = text.replace(/<\/div><\/div>/g, '</div>');
        text = text.replace(/^<\/div>/, '');
        
        // Replace markdown-style headers
        text = text.replace(/^\s*#{4}\s+(.+)$/gm, '<h4>$1</h4>');
        text = text.replace(/^\s*#{3}\s+(.+)$/gm, '<h3>$1</h3>');
        text = text.replace(/^\s*#{2}\s+(.+)$/gm, '<h2>$1</h2>');
        text = text.replace(/^\s*#{1}\s+(.+)$/gm, '<h1>$1</h1>');
        
        // Replace bold text (but not if already replaced as section headers)
        text = text.replace(/\*\*([^*<]+)\*\*/g, '<strong>$1</strong>');
        
        // Replace italic text
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Replace price ranges with highlighted spans
        text = text.replace(/\$(\d{1,3}(,\d{3})*(\.\d+)?)\s*(-|to)\s*\$(\d{1,3}(,\d{3})*(\.\d+)?)/g, 
                          '<span class="price-range">$$$1 - $$$5</span>');
        
        // Add a wrapper for the first overview paragraph
        const firstParagraphEnd = text.indexOf('</div>');
        if (firstParagraphEnd > 0) {
            const overview = text.substring(0, firstParagraphEnd);
            if (!overview.includes('<div class="')) {
                text = '<div class="putter-overview">' + overview + '</div>' + text.substring(firstParagraphEnd);
            }
        }
        
        // COMPLETELY REVISED APPROACH TO LIST FORMATTING
        // First convert all bullet points to the same level
        // Find all bullet points, regardless of indentation level
        text = text.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
        
        // Convert all nesting to a flat structure
        // Find all areas with multiple consecutive <li> elements and wrap them in a single <ul>
        const items = text.match(/(<li>.*?<\/li>)+/g) || [];
        
        items.forEach(itemGroup => {
            // Replace the item group with a properly wrapped <ul> containing all items
            const wrapped = `<ul class="bullet-list">${itemGroup}</ul>`;
            text = text.replace(itemGroup, wrapped);
        });
        
        // Clean up any remaining unclosed or unpaired list tags
        text = text.replace(/<\/ul><ul class="bullet-list">/g, '');
        
        // Create consistent key-value pairs for specifications and basic info
        text = text.replace(/^([^:<]+):\s*(.+)$/gm, '<div class="info-row"><span class="info-label">$1:</span> <span class="info-value">$2</span></div>');
        
        // Convert line breaks to paragraphs (if not already in a special format)
        const paragraphs = text.split(/\n\s*\n/);
        text = paragraphs.map(p => {
            // If it's a list or already has HTML, don't wrap in <p>
            if (p.includes('<li>') || p.match(/<[a-z][\s\S]*>/i)) {
                return p;
            }
            return `<p>${p}</p>`;
        }).join('');
        
        // Ensure all sections are properly closed
        if (text.match(/<div class="[^"]*section/g) && 
            text.match(/<div class="[^"]*section/g).length > text.match(/<\/div>/g).length) {
            text += '</div>';
        }
        
        return text;
    }
}); 