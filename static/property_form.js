async function refreshTalukas() {
  const districtEl = document.getElementById("id_district");
  const talukaList = document.getElementById("taluka-list");
  if (!districtEl || !talukaList) return;

  const district = districtEl.value || "";
  talukaList.innerHTML = "";
  if (!district) return;

  try {
    const resp = await fetch(`/api/talukas/?district=${encodeURIComponent(district)}`);
    const data = await resp.json();
    (data.talukas || []).forEach(t => {
      const opt = document.createElement("option");
      opt.value = t;
      talukaList.appendChild(opt);
    });
  } catch (e) {}
}

document.addEventListener("DOMContentLoaded", () => {
  const districtEl = document.getElementById("id_district");
  if (districtEl) {
    districtEl.addEventListener("change", refreshTalukas);
    refreshTalukas();
  }
});
