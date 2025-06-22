import { marked } from "marked"; // Import the markdown converter

// Handle rendering
window.addEventListener('load', () => {
    const contentDivs = document.getElementsByClassName("markdown_post");
    for (var div of contentDivs) {
        const markdownText = div.innerHTML;
        const htmlOutput = marked(markdownText);
        div.innerHTML = htmlOutput;
        div.style.display = "block";
    }
});