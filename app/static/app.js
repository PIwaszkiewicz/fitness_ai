// Logika strony: pobiera pytania z API, buduje z nich formularz, obsługuje pytania
// warunkowe, wysyła odpowiedzi i wyświetla wynik wywiadu oraz plan treningowy.

const API = "/api/v1";

const LEVEL_NAMES = {
  beginner: "Początkujący",
  intermediate: "Średniozaawansowany",
  advanced: "Zaawansowany",
};

const MUSCLE_GROUP_NAMES = {
  chest: "Klatka piersiowa",
  back: "Plecy",
  shoulders: "Barki",
  arms: "Ramiona",
  legs: "Nogi",
  glutes: "Pośladki",
  core: "Brzuch i tułów",
  full_body: "Całe ciało",
};

const CLASSIFIER_NAMES = {
  rules: "System regułowy",
  decision_tree: "Drzewo decyzyjne",
  mlp: "Sieć neuronowa (MLP)",
};

let questions = []; // definicja pytań pobrana z API
let profileId = null; // id profilu zapisanego po wysłaniu kwestionariusza

const form = document.getElementById("questionnaire-form");
const classifierSelect = document.getElementById("classifier");

// ---------- Komunikacja z API ----------

// Wysyła żądanie do API i zwraca odpowiedź jako obiekt. Przy błędzie rzuca wyjątek
// z kodem HTTP i szczegółami (np. listą błędów walidacji przy kodzie 422).
async function request(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error("Błąd serwera (" + response.status + ")");
    error.status = response.status;
    error.detail = data.detail;
    throw error;
  }
  return data;
}

// ---------- Pomocnicze ----------

// Zamienia znaki specjalne HTML na bezpieczne odpowiedniki. Każdy tekst z API wstawiany
// do strony przechodzi przez tę funkcję, więc nie da się w ten sposób wstrzyknąć kodu (XSS).
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function findQuestion(id) {
  return questions.find((question) => question.id === id);
}

// Polska nazwa wartości słownikowej (np. sprzętu) na podstawie opcji z definicji pytań.
function optionLabel(questionId, value) {
  const question = findQuestion(questionId);
  const option = question && question.options.find((item) => item.value === value);
  return option ? option.label : value;
}

// ---------- Budowa formularza ----------

// Tworzy pole formularza odpowiednie do typu pytania.
function createField(question) {
  const wrapper = document.createElement("div");
  wrapper.className = "field";
  wrapper.dataset.question = question.id;

  const star = question.required ? ' <span class="required">*</span>' : "";
  let html = "";

  if (question.type === "integer" || question.type === "number") {
    const step = question.type === "integer" ? 1 : 0.1;
    html = `
      <label class="field-label" for="${question.id}">${escapeHtml(question.text)}${star}</label>
      <div class="input-row">
        <input type="number" id="${question.id}" name="${question.id}"
               min="${question.min}" max="${question.max}" step="${step}"
               ${question.required ? "required" : ""}>
        <span class="muted">${escapeHtml(question.unit || "")}</span>
      </div>`;
  } else if (question.type === "choice") {
    const options = question.options
      .map((option) => `<option value="${option.value}">${escapeHtml(option.label)}</option>`)
      .join("");
    html = `
      <label class="field-label" for="${question.id}">${escapeHtml(question.text)}${star}</label>
      <select id="${question.id}" name="${question.id}" ${question.required ? "required" : ""}>
        <option value="">— wybierz —</option>${options}
      </select>`;
  } else if (question.type === "multi_choice") {
    const options = question.options
      .map((option) => `
        <label><input type="checkbox" name="${question.id}" value="${option.value}">
        ${escapeHtml(option.label)}</label>`)
      .join("");
    html = `
      <span class="field-label">${escapeHtml(question.text)}${star}</span>
      <div class="options">${options}</div>`;
  } else if (question.type === "boolean") {
    html = `
      <span class="field-label">${escapeHtml(question.text)}${star}</span>
      <div class="options">
        <label><input type="radio" name="${question.id}" value="true"> Tak</label>
        <label><input type="radio" name="${question.id}" value="false"> Nie</label>
      </div>`;
  }

  if (question.hint) {
    html += `<p class="hint">${escapeHtml(question.hint)}</p>`;
  }
  wrapper.innerHTML = html;
  return wrapper;
}

// Grupuje pytania według sekcji i wstawia je do strony.
function renderQuestions() {
  const container = document.getElementById("questions");
  container.innerHTML = "";
  const sections = {};
  for (const question of questions) {
    if (!sections[question.section]) {
      const fieldset = document.createElement("fieldset");
      fieldset.innerHTML = `<legend>${escapeHtml(question.section)}</legend>`;
      container.appendChild(fieldset);
      sections[question.section] = fieldset;
    }
    sections[question.section].appendChild(createField(question));
  }
}

// ---------- Odczyt odpowiedzi i pytania warunkowe ----------

// Zwraca odpowiedź na pytanie w formacie oczekiwanym przez API (null = brak odpowiedzi).
function readValue(question) {
  if (question.type === "multi_choice") {
    const checked = form.querySelectorAll(`input[name="${question.id}"]:checked`);
    return Array.from(checked).map((input) => input.value);
  }
  if (question.type === "boolean") {
    const checked = form.querySelector(`input[name="${question.id}"]:checked`);
    return checked ? checked.value === "true" : null;
  }
  const value = form.elements[question.id].value;
  if (value === "") {
    return null;
  }
  return question.type === "choice" ? value : Number(value);
}

// Sprawdza warunek show_if: czy pole z warunku zawiera którąś z wymaganych wartości.
function isShown(question) {
  if (!question.show_if) {
    return true;
  }
  const selected = readValue(findQuestion(question.show_if.field)) || [];
  return selected.some((value) => question.show_if.any_of.includes(value));
}

// Pokazuje lub ukrywa pytania warunkowe. Ukryte pola są wyłączane (disabled),
// więc przeglądarka ich nie waliduje, a ich odpowiedzi nie trafiają do API.
function updateVisibility() {
  for (const question of questions) {
    const wrapper = form.querySelector(`[data-question="${question.id}"]`);
    const shown = isShown(question);
    wrapper.hidden = !shown;
    wrapper.querySelectorAll("input, select").forEach((input) => {
      input.disabled = !shown;
    });
  }
}

// Zbiera odpowiedzi do wysłania, pomijając pytania ukryte i bez odpowiedzi.
function collectAnswers() {
  const answers = {};
  for (const question of questions) {
    const value = readValue(question);
    if (!isShown(question) || value === null) {
      continue;
    }
    // Pusta lista sprzętu oznacza brak odpowiedzi (API wymaga co najmniej jednej pozycji).
    if (Array.isArray(value) && value.length === 0 && question.id !== "limitations") {
      continue;
    }
    answers[question.id] = value;
  }
  return answers;
}

// Wyświetla błędy walidacji z API (kod 422) przy nazwach pytań, których dotyczą.
function showErrors(error) {
  const box = document.getElementById("form-errors");
  let messages = [error.message];
  if (error.status === 422 && Array.isArray(error.detail)) {
    messages = error.detail.map((item) => {
      const question = findQuestion(item.loc[1]);
      return question ? `${question.text}: ${item.msg}` : item.msg;
    });
  }
  box.innerHTML = "<ul>" + messages.map((text) => `<li>${escapeHtml(text)}</li>`).join("") + "</ul>";
  box.hidden = false;
  box.scrollIntoView({ behavior: "smooth", block: "center" });
}

// ---------- Wynik wywiadu i plan ----------

function renderSummary(result) {
  const profile = result.profile;
  let html = "";
  if (result.warnings.length) {
    html += '<div class="alert alert-warning"><strong>Ważne:</strong><ul>'
      + result.warnings.map((text) => `<li>${escapeHtml(text)}</li>`).join("")
      + "</ul></div>";
  }
  html += `<div class="card"><h2>Twój profil</h2>
    <p>Kompletność danych: <strong>${profile.data_completeness}%</strong></p>`;
  if (result.missing_answers.length) {
    const missing = result.missing_answers.map((id) => escapeHtml(findQuestion(id).text));
    html += `<p class="muted">Odpowiedź na te pytania pozwoli lepiej dopasować plan:</p>
      <ul class="muted">${missing.map((text) => `<li>${text}</li>`).join("")}</ul>`;
  }
  html += "</div>";
  document.getElementById("summary").innerHTML = html;
}

// Polska odmiana: 1 trening, 2–4 treningi, 5 i więcej treningów (ale 22–24 treningi).
function trainingsLabel(count) {
  if (count === 1) {
    return "1 trening";
  }
  const lastDigit = count % 10;
  const lastTwo = count % 100;
  const few = lastDigit >= 2 && lastDigit <= 4 && (lastTwo < 12 || lastTwo > 14);
  return `${count} ${few ? "treningi" : "treningów"}`;
}

function renderProbabilities(probabilities) {
  // Kolejność od najniższego poziomu (API zwraca poziomy alfabetycznie).
  return Object.keys(LEVEL_NAMES)
    .map((level) => {
      const percent = Math.round(probabilities[level] * 100);
      return `<div class="probability">
          <span>${LEVEL_NAMES[level]}</span>
          <div class="bar"><div class="bar-fill" style="width: ${percent}%"></div></div>
          <span>${percent}%</span>
        </div>`;
    })
    .join("");
}

function renderDay(day) {
  const rows = day.exercises
    .map((exercise) => `<tr>
        <td>${escapeHtml(exercise.name)}<br>
          <span class="muted">${escapeHtml(optionLabel("available_equipment", exercise.equipment))}</span></td>
        <td>${MUSCLE_GROUP_NAMES[exercise.muscle_group]}</td>
        <td>${exercise.sets} × ${escapeHtml(exercise.reps)}</td>
        <td>${exercise.rest_seconds} s</td>
      </tr>`)
    .join("");
  return `<div class="card">
      <h3>Dzień ${day.day}: ${escapeHtml(day.focus)}</h3>
      <table>
        <thead><tr><th>Ćwiczenie</th><th>Partia</th><th>Serie × powt.</th><th>Przerwa</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="4">Brak ćwiczeń</td></tr>'}</tbody>
      </table>
    </div>`;
}

function renderPlan(plan, probabilities, requestedMethod) {
  let html = `<div class="card">
      <h2>Poziom sprawności: <span class="level">${LEVEL_NAMES[plan.fitness_level]}</span></h2>
      <p class="muted">Wyznaczony przez: ${CLASSIFIER_NAMES[plan.classifier]}</p>`;
  if (plan.classifier !== requestedMethod) {
    html += '<p class="muted">Wybrany model nie jest wytrenowany, dlatego użyto systemu regułowego.</p>';
  }
  if (probabilities) {
    html += "<p>Pewność modelu:</p>" + renderProbabilities(probabilities);
  }
  html += `</div>
    <div class="card"><h2>Twój plan</h2>
      <p>${trainingsLabel(plan.days_per_week)} w tygodniu, około ${plan.session_minutes} minut
      (w tym 10 minut rozgrzewki).</p>`;
  if (plan.excluded_for_safety > 0) {
    html += `<p class="muted">Ze względu na zgłoszone ograniczenia pominięto ćwiczeń:
      ${plan.excluded_for_safety}.</p>`;
  }
  html += "</div>";
  html += plan.days.map(renderDay).join("");
  html += '<div class="card"><h2>Jak robić postępy</h2><ul>'
    + plan.progression.map((text) => `<li>${escapeHtml(text)}</li>`).join("")
    + "</ul></div>";
  document.getElementById("plan").innerHTML = html;
}

// Pobiera plan wybranym klasyfikatorem. Pewność modelu (prawdopodobieństwa) jest dostępna
// tylko dla modeli ML, więc pobieramy ją, gdy plan nie powstał z systemu regułowego.
async function loadPlan() {
  const method = classifierSelect.value;
  const planBox = document.getElementById("plan");
  planBox.innerHTML = '<p class="muted">Wczytywanie planu…</p>';
  try {
    const plan = await request(`/profiles/${profileId}/plan?method=${method}`);
    let probabilities = null;
    if (plan.classifier !== "rules") {
      const level = await request(`/profiles/${profileId}/fitness-level?method=${plan.classifier}`);
      probabilities = level.probabilities;
    }
    renderPlan(plan, probabilities, method);
  } catch (error) {
    planBox.innerHTML = `<div class="alert alert-error">${escapeHtml(error.message)}</div>`;
  }
}

function showView(name) {
  document.getElementById("questionnaire-view").hidden = name !== "questionnaire";
  document.getElementById("result-view").hidden = name !== "result";
  window.scrollTo({ top: 0 });
}

// ---------- Obsługa zdarzeń ----------

form.addEventListener("change", updateVisibility);

form.addEventListener("submit", async (event) => {
  event.preventDefault(); // zamiast przeładowania strony wysyłamy dane przez fetch
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  document.getElementById("form-errors").hidden = true;
  try {
    const result = await request("/questionnaire", {
      method: "POST",
      body: JSON.stringify(collectAnswers()),
    });
    profileId = result.profile.id;
    renderSummary(result);
    showView("result");
    await loadPlan();
  } catch (error) {
    showErrors(error);
  } finally {
    button.disabled = false;
  }
});

classifierSelect.addEventListener("change", loadPlan);

document.getElementById("restart").addEventListener("click", () => {
  form.reset();
  updateVisibility();
  showView("questionnaire");
});

// ---------- Start strony ----------

async function init() {
  try {
    questions = await request("/questionnaire");
    renderQuestions();
    updateVisibility();
  } catch (error) {
    document.getElementById("questions").innerHTML =
      `<div class="alert alert-error">Nie udało się pobrać pytań: ${escapeHtml(error.message)}</div>`;
  }
}

init();
