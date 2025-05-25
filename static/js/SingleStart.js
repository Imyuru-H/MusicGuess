document.addEventListener("DOMContentLoaded", async function() {
    try {
        const response = await fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status:true })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();  // 确保 response 是 JSON
        console.log('Success:', data);
    } catch (error) {
        console.error('Erroe:', error);
    }
});