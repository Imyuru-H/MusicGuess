function handleChoice(choice = 0) {
    const choiceEvent = new CustomEvent('choiceEvent', { detail: {index: choice} });
    console.log(`choice: ${choice}`);
    document.dispatchEvent(choiceEvent);
}

async function submit(song = null) {
    const input = document.getElementById('input').value
    document.getElementById('input').value = ''

    const table = document.getElementById('guess-table')
    const dialog = document.getElementById('custom-dialog')
    let data
    
    try {
        const response = await fetch('/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: song || input })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();  // 确保 response 是 JSON
        console.log('Success:', data);

        // 把信息呈现在表格里
        if (data['status'] && data['title'].length == 1) {
            table.insertAdjacentHTML('beforeend', data['html'][0]);
        } else if (data['status'] && data['title'].length > 1) {
            dialog.querySelectorAll('button').forEach(child => {
                child.remove();
            });
            for (let i = 0; i < data['title'].length; i++) {
                dialog.insertAdjacentHTML('beforeend', `<button id="choice" onclick="handleChoice(${i})">${data['title'][i]}</button>`)
            }
            dialog.style.display = 'block';

            document.addEventListener('choiceEvent', (e) => {
                dialog.style.display = 'none';
                submit(data['title'][e.detail.index]);
            });
        } else if ('error' in data) {
            alert(data['error']);
        }
    } catch (error) {
        console.error('Error:', error);
    } 
}