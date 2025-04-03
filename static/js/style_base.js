    lucide.createIcons();

    const toggleBtn = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");
    const topbar = document.getElementById("topbar");
    const mainContent = document.getElementById("main-content");
    const overlay = document.getElementById("overlay");

    toggleBtn.addEventListener("click", () => {
      const isMobile = window.innerWidth <= 768;

      if (isMobile) {
        sidebar.classList.toggle("active");
        overlay.classList.toggle("active");
      } else {
        sidebar.classList.toggle("collapsed");
        topbar.classList.toggle("collapsed");
        mainContent.classList.toggle("collapsed");
      }
    });

    overlay.addEventListener("click", () => {
      sidebar.classList.remove("active");
      overlay.classList.remove("active");
    });