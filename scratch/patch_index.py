import os

html_path = r"producao/templates/producao/index.html"

def main():
    if not os.path.exists(html_path):
        print("HTML file not found!")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add CSS style for Edit Modal
    print("Patching CSS styles...")
    css_target = "        body.alerting .alert-overlay {\n            animation: alertFlash 1s steps(1) infinite;\n        }"
    css_replacement = """        body.alerting .alert-overlay {
            animation: alertFlash 1s steps(1) infinite;
        }
        
        /* ---------- Modal CSS ---------- */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(16, 23, 42, 0.45);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }
        .modal-overlay.show {
            opacity: 1;
            pointer-events: auto;
        }
        .modal-content {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 24px;
            width: 90%;
            max-width: 360px;
            transform: translateY(10px);
            transition: transform 0.2s ease;
        }
        .modal-overlay.show .modal-content {
            transform: translateY(0);
        }
        .btn-edit:hover {
            background-color: var(--gray-bg);
        }"""
    if css_target in html:
        html = html.replace(css_target, css_replacement)
    else:
        print("Warning: CSS target not found.")

    # 2. Remove interval-row selector from HTML
    print("Removing interval selector...")
    interval_row_markup = """        <div class="interval-row">
            <span>Intervalo de apontamento</span>
            <select id="intervalSelect">
                <option value="120000" selected>2 min (teste)</option>
                <option value="3600000">60 min (produção)</option>
            </select>
        </div>"""
    if interval_row_markup in html:
        html = html.replace(interval_row_markup, "")
    else:
        # Fallback to search by parts if whitespace is different
        print("Warning: Interval row markup not found.")

    # 3. Add Modal overlay markup before </body>
    print("Adding modal HTML markup...")
    modal_markup = """    <!-- EDIT MODAL -->
    <div class="modal-overlay" id="editModal">
        <div class="modal-content">
            <h2 style="font-size: 16px; font-weight: 700; color: var(--blue); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Editar Apontamento</h2>
            <div class="field">
                <label for="editQtdInput">Nova Quantidade Produzida</label>
                <input id="editQtdInput" type="number" min="1" class="mono" placeholder="Digite a nova quantidade">
            </div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn btn-stop" id="cancelEditBtn" style="background: var(--gray-bg); color: var(--ink); flex: 1;">Cancelar</button>
                <button class="btn btn-primary" id="saveEditBtn" style="flex: 1;">Salvar</button>
            </div>
        </div>
    </div>\n\n</body>"""
    html = html.replace("</body>", modal_markup)

    # 4. Modify JavaScript state variables and elements
    print("Patching JS elements and variables...")
    js_vars_target = """            let status = 'idle'; // idle | running | occurrence | auth-error
            let active = null;   // { op, cliente, produto, matricula, recurso, start, occurrences:[] }
            let occ = null;       // { motivo, start }
            let log = [];
            let intervalMs = 120000;     // apontamento cadence — 2 min in test mode, 60 min in production
            let lastApontamentoAt = null;
            let alerting = false;"""
            
    js_vars_replacement = """            let status = 'idle'; // idle | running | occurrence | auth-error
            let active = null;   // { op, cliente, produto, matricula, recurso, start, occurrences:[] }
            let occ = null;       // { motivo, start }
            let log = [];
            let lastApontamentoAt = null;
            let alerting = false;"""
            
    html = html.replace(js_vars_target, js_vars_replacement)
    
    js_el_target = "            const intervalSelect = $('intervalSelect'), alertOverlay = $('alertOverlay');"
    js_el_replacement = "            const alertOverlay = $('alertOverlay');"
    html = html.replace(js_el_target, js_el_replacement)

    # 5. Remove intervalSelect event listener
    print("Removing intervalSelect event listener...")
    listener_target = """            // ---------- Apontamento cadence & alert ----------
            intervalSelect.addEventListener('change', () => {
                intervalMs = Number(intervalSelect.value);
            });"""
    html = html.replace(listener_target, "            // ---------- Apontamento cadence & alert ----------")

    # 6. Replace checkApontamento with hourly turn logic
    print("Replacing checkApontamento logic...")
    check_target = """            function checkApontamento(now) {
                if (status === 'idle' || !active || status === 'auth-error') {
                    nextTimer.textContent = '--:--:--';
                    if (alerting) clearAlert();
                    return;
                }
                const remaining = intervalMs - (now - lastApontamentoAt);
                if (remaining <= 0) {
                    if (!alerting) {
                        alerting = true;
                        document.body.classList.add('alerting');
                        nextBadge.classList.add('overdue');
                    }
                    nextTimer.textContent = 'Atrasado';
                } else {
                    nextTimer.textContent = fmtDuration(remaining);
                }
            }"""
            
    check_replacement = """            function getDeadline(baseDate) {
                const d = new Date(baseDate.getTime());
                d.setHours(d.getHours() + 1, 0, 0, 0);
                return d;
            }

            function checkApontamento(now) {
                if (status === 'idle' || !active || status === 'auth-error') {
                    nextTimer.textContent = '--:--:--';
                    if (alerting) clearAlert();
                    return;
                }
                const deadline = getDeadline(lastApontamentoAt);
                const remaining = deadline - now;
                if (remaining <= 0) {
                    if (!alerting) {
                        alerting = true;
                        document.body.classList.add('alerting');
                        nextBadge.classList.add('overdue');
                    }
                    nextTimer.textContent = 'Atrasado';
                } else {
                    if (alerting) clearAlert();
                    nextTimer.textContent = fmtDuration(remaining);
                }
            }"""
    html = html.replace(check_target, check_replacement)

    # 7. Add confirmation prompt on finalizeBtn click
    print("Adding confirmation prompt on OP finalization...")
    finalize_click_target = """            finalizeBtn.addEventListener('click', async () => {
                const end = new Date();"""
    finalize_click_replacement = """            finalizeBtn.addEventListener('click', async () => {
                if (encerrarCheck.checked) {
                    const confirmClose = confirm("Deseja realmente encerrar esta Ordem de Produção? Esta ação não pode ser desfeita.");
                    if (!confirmClose) {
                        return;
                    }
                }
                const end = new Date();"""
    html = html.replace(finalize_click_target, finalize_click_replacement)

    # 8. Update buildLogRow to include editIndex and edit button
    print("Modifying buildLogRow function...")
    build_row_target = """            // ---------- Log rendering ----------
            function buildLogRow({ type, title, sub, time, dur }) {
                const row = document.createElement('div');
                row.className = 'log-row t-' + type;
                const icon = type === 'producao'
                    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
                    : iconAlert();
                row.innerHTML = `
                  <div class="l-icon">${icon}</div>
                  <div class="l-main">
                    <div class="l-title">${title}</div>
                    <div class="l-sub">${sub}</div>
                  </div>
                  <div class="l-time">${time}</div>
                  <div class="l-dur">${dur}</div>`;
                return row;
            }"""
            
    build_row_replacement = """            // ---------- Log rendering ----------
            function buildLogRow({ type, title, sub, time, dur, editIndex = null }) {
                const row = document.createElement('div');
                row.className = 'log-row t-' + type;
                const icon = type === 'producao'
                    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
                    : iconAlert();
                    
                const editButtonHtml = (type === 'producao' && editIndex !== null)
                    ? `<button class="btn-edit" data-index="${editIndex}" style="background: none; border: none; padding: 4px; cursor: pointer; color: var(--blue); margin-left: 12px; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 6px;" title="Editar quantidade">
                         <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                       </button>`
                    : '';

                row.innerHTML = `
                  <div class="l-icon">${icon}</div>
                  <div class="l-main">
                    <div class="l-title">${title}</div>
                    <div class="l-sub">${sub}</div>
                  </div>
                  <div class="l-time">${time}</div>
                  <div class="l-dur" style="display: flex; align-items: center; gap: 8px;">
                    <span>${dur}</span>
                    ${editButtonHtml}
                  </div>`;
                return row;
            }"""
    html = html.replace(build_row_target, build_row_replacement)

    # 9. Update renderLog to bind click event to the edit button
    print("Modifying renderLog function...")
    render_log_target = """            function renderLog() {
                if (log.length === 0) {
                    logList.innerHTML = '';
                    logList.appendChild(logEmpty);
                    logEmpty.style.display = 'block';
                    return;
                }
                logList.innerHTML = '';
                log.forEach(e => {
                    logList.appendChild(buildLogRow({
                        type: 'producao',
                        title: `OP ${e.op} · ${e.produto}`,
                        sub: `${e.cliente} · Matrícula ${e.matricula} · ${e.recurso}${e.encerrouOP ? ' · OP encerrada' : ''}`,
                        time: `${fmtClock(e.start)} → ${fmtClock(e.end)}`,
                        dur: `${e.quantidade} un · ${fmtDuration(e.duration)}`
                    }));
                });
            }"""
            
    render_log_replacement = """            function renderLog() {
                if (log.length === 0) {
                    logList.innerHTML = '';
                    logList.appendChild(logEmpty);
                    logEmpty.style.display = 'block';
                    return;
                }
                logList.innerHTML = '';
                log.forEach((e, idx) => {
                    const row = buildLogRow({
                        type: 'producao',
                        title: `OP ${e.op} · ${e.produto}`,
                        sub: `${e.cliente} · Matrícula ${e.matricula} · ${e.recurso}${e.encerrouOP ? ' · OP encerrada' : ''}`,
                        time: `${fmtClock(e.start)} → ${fmtClock(e.end)}`,
                        dur: `${e.quantidade} un · ${fmtDuration(e.duration)}`,
                        editIndex: idx
                    });
                    
                    const editBtn = row.querySelector('.btn-edit');
                    if (editBtn) {
                        editBtn.addEventListener('click', (event) => {
                            event.stopPropagation();
                            openEditModal(idx);
                        });
                    }
                    
                    logList.appendChild(row);
                });
            }"""
    html = html.replace(render_log_target, render_log_replacement)

    # 10. Append edit modal control logic at the bottom of JS script block
    print("Adding edit modal JS control code...")
    js_modal_code = """            // ---------- Edit Modal Logic ----------
            let editingIndex = null;
            const editModal = $('editModal'), editQtdInput = $('editQtdInput');
            const cancelEditBtn = $('cancelEditBtn'), saveEditBtn = $('saveEditBtn');
            
            function openEditModal(index) {
                editingIndex = index;
                const entry = log[index];
                editQtdInput.value = entry.quantidade;
                editModal.classList.add('show');
            }
            
            function closeEditModal() {
                editingIndex = null;
                editModal.classList.remove('show');
            }
            
            cancelEditBtn.addEventListener('click', closeEditModal);
            
            saveEditBtn.addEventListener('click', async () => {
                if (editingIndex === null) return;
                
                const newQtd = Number(editQtdInput.value);
                if (isNaN(newQtd) || newQtd <= 0) {
                    alert('Por favor, insira uma quantidade válida maior que zero.');
                    return;
                }
                
                const entry = log[editingIndex];
                
                saveEditBtn.disabled = true;
                const originalText = saveEditBtn.innerHTML;
                saveEditBtn.innerHTML = 'Salvando...';
                
                try {
                    const payload = {
                        filter: {
                            op_id: entry.op,
                            data: fmtDate(entry.end),
                            hora: fmtTime(entry.end),
                            matricula: entry.matricula,
                            maquina: entry.recurso
                        },
                        new_quantidade: newQtd
                    };
                    
                    const response = await fetch('/api/apontamentos/edit/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    const data = await response.json();
                    if (!response.ok) {
                        throw new Error(data.message || 'Falha ao atualizar o apontamento no Google Sheets.');
                    }
                    
                    // Update locally
                    entry.quantidade = newQtd;
                    
                    // Re-render
                    renderLog();
                    closeEditModal();
                    showToast('Apontamento atualizado com sucesso!');
                    
                } catch (e) {
                    alert('Erro ao atualizar quantidade: ' + e.message);
                } finally {
                    saveEditBtn.disabled = false;
                    saveEditBtn.innerHTML = originalText;
                }
            });

            // Start clock ticks"""
            
    html = html.replace("// Start clock ticks", js_modal_code)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML script patch applied successfully!")

if __name__ == "__main__":
    main()
