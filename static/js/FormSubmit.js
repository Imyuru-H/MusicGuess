function parse_data(data) {
    const title = data['title'];
    const artist = data['artist'];
    const bpm = data['bpm'];
    const difficulty = data['difficulty'];
    const level = data['level'];
    const note_count = data['note count'].at(-1);
    const chapter = data['pack'];

    let has_at
    if (difficulty.length == 4) {
        has_at = '✅'
    } else {
        has_at = '❌'
    }

    html = '<tr id="column">' + 
           `    <td>${title}</td>` + 
           `    <td>${artist}</td>` + 
           `    <td>${bpm}</td>` + 
           `    <td>${has_at}</td>` + 
           `    <td>` + 
           `        <span>${level[0]}</span>` + 
           `        <span>${level[1]}</span>` + 
           `        <span>${level[2]}</span>` + 
           `        ${level.length==4 ? `<span>${level[3]}</span>` : ''}` + 
           `    </td>` + 
           `    <td>${note_count}</td>` + 
           `    <td>${chapter}</td>` + 
           `</tr>`;
    
    return html
}

async function submit() {
    const input = document.getElementById('input').value
    const table = document.getElementById('guess-table')
    let data, html
    
    try {
        const response = await fetch('/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: input })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();  // 确保 response 是 JSON
        console.log('Success:', data);
    } catch (error) {
        console.error('Erroe:', error);
    }

    // 把信息呈现在表格里
    if (data['status']) {
        html = parse_data(data);
        table.insertAdjacentHTML('beforeend', html);
    }
}