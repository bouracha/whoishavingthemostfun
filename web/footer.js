// Footer injection script - adds contact footer to all pages
function injectFooter() {
    const footer = `
        <footer style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-top: 1px solid #e9ecef; text-align: center; color: #6c757d; font-size: 14px;">
            <div style="max-width: 800px; margin: 0 auto;">
                <p style="margin: 0 0 10px 0;">
                    <strong>Who's Having The Most Fun?</strong> - ELO Rating System
                </p>
                <p style="margin: 0;">
                    Contact: <a href="mailto:bouracha@tcd.ie" style="color: #007bff; text-decoration: none;">bouracha@tcd.ie</a>
                </p>
            </div>
        </footer>
    `;
    
    // Insert footer before closing body tag
    document.body.insertAdjacentHTML('beforeend', footer);
}

// Inject footer when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectFooter);
} else {
    injectFooter();
}
