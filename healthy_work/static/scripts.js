document.addEventListener("DOMContentLoaded", () => {
    const fechaInput = document.getElementById("fecha");
    const horaSelect = document.getElementById("hora");

    if (!fechaInput) {
        console.warn("No se encontró el campo fecha (#fecha). ¿Estás en agenda.html?");
        return;
    }

    // 🔹 Bloquear fines de semana
    fechaInput.addEventListener("input", () => {
        const dia = new Date(fechaInput.value).getUTCDay();
        if (dia === 0 || dia === 6) {
            fechaInput.value = "";
        }
    });

    // 🔹 Cargar horarios dinámicamente sin refrescar
    fechaInput.addEventListener("change", function () {
        const fecha = this.value;

        if (!fecha) return;

        fetch(`/horarios_disponibles?fecha=${fecha}`)
            .then(res => res.json())
            .then(data => {
                horaSelect.innerHTML = "";

                if (data.horarios.length === 0) {
                    horaSelect.innerHTML = "<option value=''>No hay horarios disponibles</option>";
                    return;
                }

                data.horarios.forEach(h => {
                    const option = document.createElement("option");
                    option.value = h;
                    option.textContent = h;
                    horaSelect.appendChild(option);
                });
            })
            .catch(err => console.error("Error cargando horarios:", err));
    });
});
