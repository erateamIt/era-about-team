document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector("#dashboard-sidebar");
    const toggle = document.querySelector(".sidebar-toggle");
    const overlay = document.querySelector(".sidebar-overlay");

    if (!sidebar || !toggle || !overlay) return;

    const closeSidebar = () => {
        sidebar.classList.remove("sidebar-open");
        overlay.classList.remove("visible");
        toggle.setAttribute("aria-expanded", "false");
    };

    toggle.addEventListener("click", () => {
        const isOpen = sidebar.classList.toggle("sidebar-open");
        overlay.classList.toggle("visible", isOpen);
        toggle.setAttribute("aria-expanded", String(isOpen));
    });
    overlay.addEventListener("click", closeSidebar);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeSidebar();
    });
});
