# --- DEBUG HELPERS (tymczasowe, usuń po testach) ---
@app.route('/admin/whoami', methods=['GET'])
def admin_whoami():
    """Return current server ADMIN_TELEGRAM_ID for debugging"""
    return jsonify({'admin_telegram_id': ADMIN_TELEGRAM_ID}), 200

@app.route('/admin/debug-add-tickets', methods=['POST'])
def admin_debug_add_tickets():
    """
    Debug endpoint: echo back received payload/headers and attempt add-tickets behavior.
    Use only for debugging on Railway; remove afterwards.
    """
    data = request.json or {}
    admin_id = data.get('admin_telegram_id') or request.headers.get('X-Admin-Telegram')
    target = data.get('target_telegram_id')
    amount = data.get('amount', 1)

    # Build debug echo
    echo = {
        'received_json': data,
        'received_headers': {k: v for k, v in request.headers.items() if k.lower().startswith('x-') or k.lower().startswith('content-')},
        'admin_id_raw': admin_id,
        'target_raw': target,
        'amount_raw': amount
    }

    # Try to coerce and run existing logic to see result
    try:
        if admin_id is None:
            echo['action'] = 'missing_admin_id'
            return jsonify(echo), 400
        admin_id_int = int(admin_id)
        echo['admin_id_int'] = admin_id_int
        echo['is_admin'] = (admin_id_int == ADMIN_TELEGRAM_ID)

        # only attempt update if admin matches
        if admin_id_int != ADMIN_TELEGRAM_ID:
            echo['action'] = 'forbidden_admin'
            return jsonify(echo), 403

        # determine target
        tgt = target if target is not None else admin_id_int
        tgt = int(tgt)
        amt = int(amount)

        # try to get user and update tickets (reuse update_user_tickets)
        u = get_user(tgt) or create_user(tgt)
        prev = u.get('tickets', 0) if u else 0
        new_tickets = prev + amt
        update_user_tickets(u['id'], new_tickets)

        echo['action'] = 'ok'
        echo['prev_tickets'] = prev
        echo['new_tickets'] = new_tickets
        return jsonify(echo), 200
    except Exception as e:
        echo['exception'] = str(e)
        return jsonify(echo), 500
# --- END DEBUG HELPERS ---
