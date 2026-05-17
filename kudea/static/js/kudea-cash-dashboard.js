document.addEventListener("DOMContentLoaded", function() {

    const btn = document.getElementById("toggle-ventas-btn");

    if (!btn) return;

    let expanded = false;

    btn.addEventListener("click", function() {

        const items = document.querySelectorAll(".venta-item");

        if (!expanded) {
            items.forEach(item => item.style.display = "flex");
            btn.textContent = "Ver menos";
            expanded = true;
        } else {
            items.forEach(item => {
                if (parseInt(item.dataset.index) > 4) {
                    item.style.display = "none";
                }
            });
            btn.textContent = "Ver más";
            expanded = false;
        }

    });

});