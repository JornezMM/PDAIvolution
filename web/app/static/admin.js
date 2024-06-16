function getData(event) {
    const clickedButton = event.target;
    const tableRow = clickedButton.closest('tr');
    const tableCells = tableRow.querySelectorAll('td');
    const rowData = {};
    for (let i = 0; i < tableCells.length; i++) {
        rowData[i] = tableCells[i].textContent.trim();
    }
    return rowData;
}

function modifyPatient(event){
    const username = getData(event)[1];
    window.location.href = `/modify/patient-` + username;
}

function modifyAdmin(event){
    const username = getData(event)[1];
    window.location.href = `/modify/admin-` + username;
}

function modifyDoctor(event){
    const username = getData(event)[1];
    window.location.href = `/modify/doctor-` + username;
}

function deletePatient(event){
    const username = getData(event)[1];
    const confirmDelete = confirm("¿Estás seguro de que deseas eliminar a este paciente?");
    if (confirmDelete) {
        window.location.href = `/delete/patient-` + username;
    }
}

function deleteAdmin(event){
    const username = getData(event)[1];
    const confirmDelete = confirm("¿Estás seguro de que deseas eliminar a este administrador?");
    if (confirmDelete) {
        window.location.href = `/delete/admin-` + username;
    }
}

function deleteDoctor(event){
    const username = getData(event)[1];
    const confirmDelete = confirm("¿Estás seguro de que deseas eliminar a este doctor?");
    if (confirmDelete) {
        window.location.href = `/delete/doctor-` + username;
    }
}
