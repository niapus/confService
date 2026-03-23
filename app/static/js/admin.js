function showSection(section) {
    document.getElementById("conferences-section").style.display =
        section === "conferences" ? "block" : "none";

    document.getElementById("theses-section").style.display =
        section === "theses" ? "block" : "none";

    document.getElementById("applications-section").style.display =
        section === "applications" ? "block" : "none";
}

document.addEventListener("DOMContentLoaded", () => {
    showSection('conferences');
    
    document.querySelectorAll('.sidebar button').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.sidebar button').forEach(b => 
                b.style.background = '#374151');
            this.style.background = '#2563eb';
        });
    });
});