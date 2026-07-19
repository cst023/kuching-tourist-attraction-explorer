// ---- Configuration ----
const API_BASE = "https://kuching-tourist-attraction-explorer.onrender.com"; 

const CATEGORY_COLORS = {
  Nature: "#03a734",
  Culture: "#ca821d",
  Landmark: "#B0553B",
  Museum: "#e3fc0a",
  Other: "#00a8eb",
};

// ---- Map setup ----
const map = L.map("map").setView([1.5533, 110.3592], 13); // Kuching city center
 
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 19,
}).addTo(map);
 
let markersLayer = L.layerGroup().addTo(map);
 
// ---- Marker rendering ----
function categoryColor(category) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.Other;
}
 
function renderMarkers(geojson) {
  markersLayer.clearLayers();
 
  geojson.features.forEach((feature) => {
    const [lng, lat] = feature.geometry.coordinates;
    const props = { ...feature.properties, lat, lng };
 
    const marker = L.circleMarker([lat, lng], {
      radius: 8,
      fillColor: categoryColor(props.category),
      fillOpacity: 0.9,
      color: "#fff",
      weight: 2,
    });
 
    marker.bindTooltip(props.name, { direction: "top", offset: [0, -6] });
    marker.on("click", () => showDetailPanel(props));
 
    marker.addTo(markersLayer);
  });
}
 
// ---- Detail panel ----
const detailPanel = document.getElementById("detailPanel");
const detailPhoto = document.getElementById("detailPhoto");
const detailCategory = document.getElementById("detailCategory");
const detailName = document.getElementById("detailName");
const detailDescription = document.getElementById("detailDescription");
const nearbySection = document.getElementById("nearbySection");
const nearbyList = document.getElementById("nearbyList");
 
const NEARBY_RADIUS_KM = 2;
 
function showDetailPanel(props) {
  detailPhoto.src = props.photo_url || "";
  detailPhoto.alt = props.name;
  detailCategory.textContent = props.category;
  detailName.textContent = props.name;
  detailDescription.textContent = props.description || "No description available.";
  detailPanel.classList.remove("hidden");
 
  // scroll panel back to top so the newly selected attraction is visible
  detailPanel.scrollTop = 0;
 
  loadNearbyAttractions(props);
}
 
async function loadNearbyAttractions(props) {
  nearbySection.classList.add("hidden");
  nearbyList.innerHTML = "";
 
  if (props.lat == null || props.lng == null) return;
 
  const params = new URLSearchParams({
    lat: props.lat,
    lng: props.lng,
    radius_km: NEARBY_RADIUS_KM,
  });
  if (props.id != null) params.set("exclude_id", props.id);
 
  try {
    const res = await fetch(`${API_BASE}/attractions/nearby?${params.toString()}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const data = await res.json();
    renderNearbyList(data.features);
  } catch (err) {
    console.error("Failed to fetch nearby attractions:", err);
  }
}
 
function renderNearbyList(features) {
  nearbySection.classList.remove("hidden");
  nearbyList.innerHTML = "";
 
  if (features.length === 0) {
    const empty = document.createElement("li");
    empty.className = "nearby-empty";
    empty.textContent = "No other attractions within 2km.";
    nearbyList.appendChild(empty);
    return;
  }
 
  features.forEach((feature) => {
    const [lng, lat] = feature.geometry.coordinates;
    const nearbyProps = { ...feature.properties, lat, lng };
 
    const li = document.createElement("li");
    li.className = "nearby-item";
 
    const info = document.createElement("div");
    info.className = "nearby-item-info";
 
    const dot = document.createElement("span");
    dot.className = "nearby-dot";
    dot.style.background = categoryColor(nearbyProps.category);
 
    const name = document.createElement("span");
    name.className = "nearby-name";
    name.textContent = nearbyProps.name;
 
    const distance = document.createElement("span");
    distance.className = "nearby-distance";
    if (typeof nearbyProps.distance_m === "number") {
      distance.textContent = nearbyProps.distance_m >= 1000
        ? `${(nearbyProps.distance_m / 1000).toFixed(1)}km`
        : `${nearbyProps.distance_m}m`;
    }
 
    info.appendChild(dot);
    info.appendChild(name);
 
    const viewLink = document.createElement("button");
    viewLink.type = "button";
    viewLink.className = "nearby-view-link";
    viewLink.textContent = "view info";
    viewLink.addEventListener("click", () => {
      showDetailPanel(nearbyProps);
      map.panTo([lat, lng]);
    });
 
    li.appendChild(info);
    li.appendChild(distance);
    li.appendChild(viewLink);
    nearbyList.appendChild(li);
  });
}
 
document.getElementById("closePanel").addEventListener("click", () => {
  detailPanel.classList.add("hidden");
});
 
// ---- Loading overlay ----
const loadingOverlay = document.getElementById("loadingOverlay");
function showLoading() { loadingOverlay.classList.remove("hidden"); }
function hideLoading() { loadingOverlay.classList.add("hidden"); }
 
// ---- Results banner ----
const resultsBanner = document.getElementById("resultsBanner");
function updateResultsBanner(count) {
  resultsBanner.textContent = `Search result: ${count} location${count === 1 ? "" : "s"} found`;
}
 
// ---- Data fetching ----
async function fetchAttractions(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE}/attractions${query ? "?" + query : ""}`;
 
  showLoading();
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const data = await res.json();
    renderMarkers(data);
    updateResultsBanner(data.features.length);
  } catch (err) {
    console.error("Failed to fetch attractions:", err);
    resultsBanner.textContent = "Search result: unable to load results";
  } finally {
    hideLoading();
  }
}
 
async function fetchCategories() {
  try {
    const res = await fetch(`${API_BASE}/categories`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const data = await res.json();
 
    const optionsList = document.getElementById("categoryOptions");
    data.categories.forEach((cat) => {
      const li = document.createElement("li");
      li.textContent = cat;
      li.dataset.value = cat;
      li.dataset.color = categoryColor(cat);
      optionsList.appendChild(li);
    });
 
    attachDropdownOptionEvents();
  } catch (err) {
    console.error("Failed to fetch categories:", err);
  }
}
 
// ---- Search wiring ----
const searchInput = document.getElementById("searchInput");
let selectedCategory = "";
 
let searchDebounce;
searchInput.addEventListener("input", () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    applyFilters();
  }, 300);
});
 
function applyFilters() {
  const params = {};
  if (searchInput.value.trim()) params.search = searchInput.value.trim();
  if (selectedCategory) params.category = selectedCategory;
  fetchAttractions(params);
}
 
// ---- Custom category dropdown wiring ----
const categoryTrigger = document.getElementById("categoryTrigger");
const categoryTriggerLabel = document.getElementById("categoryTriggerLabel");
const categoryOptions = document.getElementById("categoryOptions");
 
categoryTrigger.addEventListener("click", (e) => {
  e.stopPropagation();
  categoryOptions.classList.toggle("hidden");
});
 
document.addEventListener("click", () => {
  categoryOptions.classList.add("hidden");
});
 
function attachDropdownOptionEvents() {
  const items = categoryOptions.querySelectorAll("li");
  items.forEach((li) => {
    // hover/active color matches that category's marker color
    li.style.setProperty("--option-color", li.dataset.color);
 
    li.addEventListener("click", (e) => {
      e.stopPropagation();
      items.forEach((i) => i.classList.remove("selected"));
      li.classList.add("selected");
 
      selectedCategory = li.dataset.value;
      categoryTriggerLabel.textContent = li.textContent;
      categoryOptions.classList.add("hidden");
 
      applyFilters();
    });
  });
}
 
// ---- Init ----
attachDropdownOptionEvents(); 
fetchAttractions();
fetchCategories();