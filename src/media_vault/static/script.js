function toggleFavorite(element) {
    fetch(element.form.action, {
        method: element.form.method,
        body: new FormData(element.form),
    });
}

function toggleView() {
    let itemList = document.getElementById('item-list');
    itemList.classList.toggle("column");
}