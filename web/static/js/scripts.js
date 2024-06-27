document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([0, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);

    window.renderMap = function(routes) {
        routes.forEach(route => {
            var latlngs = route.coordinates;
            L.polyline(latlngs, { color: 'blue' }).addTo(map)
                .bindPopup('Route: ' + route.route_id);
        });
    };
});
