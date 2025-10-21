// Legal Content Lazy Loading for Footer
const loadedContent = {};

async function loadLegalContent(type) {
  // Check if already loaded
  if (loadedContent[type]) {
    return;
  }

  const contentEl = document.getElementById(`${type}-content`);

  try {
    // Fetch markdown file
    const response = await fetch(`/${type}.md`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const markdown = await response.text();

    // Render markdown to HTML
    contentEl.innerHTML = marked.parse(markdown);

    // Mark as loaded
    loadedContent[type] = true;
  } catch (error) {
    console.error(`Failed to load ${type}:`, error);
    contentEl.innerHTML = `
      <div class="alert alert-danger" role="alert">
        <h4 class="alert-title">Fehler beim Laden</h4>
        <div class="text-secondary">Der Inhalt konnte nicht geladen werden. Bitte versuchen Sie es später erneut.</div>
      </div>
    `;
  }
}
