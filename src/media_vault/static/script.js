function toggleFavorite(element) {
    fetch(element.form.action, {
        method: element.form.method,
        body: new FormData(element.form),
    });
}

function toggleView() {
    let itemList = document.getElementById('item-list');
    itemList.classList.toggle('column');
}

document.addEventListener('keyup', (e) => {
    if (e.key == 'ArrowLeft') {
        console.log('back');
        let a = document.getElementById('previous-neighbor');
        if (a) {
            let href = a.getAttribute('href');
            window.open(href, '_self');
        }
    } else if (e.key == 'ArrowRight') {
        console.log('next');
        let a = document.getElementById('next-neighbor');
        if (a) {
            let href = a.getAttribute('href');
            window.open(href, '_self');
        }
    }
});