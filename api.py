@@
 @app.route('/_config', methods=['GET'])
 def config():
-    return jsonify({'ADMIN_TELEGRAM_ID': ADMIN_TELEGRAM_ID})
+    # provide admin id and supported languages
+    return jsonify({'ADMIN_TELEGRAM_ID': ADMIN_TELEGRAM_ID, 'default_language': 'en', 'languages': ['en','pl']})
@@
 @app.route('/me', methods=['GET'])
 def me():
     telegram_id = request.args.get('telegram_id')
     if not telegram_id:
         return jsonify({'error': 'telegram_id required'}), 400
     user = db.get_user(telegram_id)
     if not user:
         return jsonify({'error': 'user not found'}), 404
-    return jsonify({'user': user})
+    # mark admin flag
+    user['is_admin'] = str(telegram_id) == str(ADMIN_TELEGRAM_ID)
+    return jsonify({'user': user})
