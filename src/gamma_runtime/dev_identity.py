from .player_identity import PlayerIdentityManager

class DevIdentityManager:
    """
    Shim for backward compatibility with the initial dev identity work.
    Proxies to the new PlayerIdentityManager.
    """
    def __init__(self, root_dir: str):
        self.manager = PlayerIdentityManager(root_dir)

    def sign_up(self, username, password, display_name=None, tags=None):
        return self.manager.sign_up(username, password, display_name)

    def sign_in(self, username, password):
        return self.manager.sign_in(username, password)

    def bind_provider(self, username, provider_url, model_id, api_key_ref, transport):
        account = self.manager.sign_in(username, "dummy") # This won't work for binding if not signed in
        # We need the account_id
        accounts = {a['username']: a for a in self.manager.list_accounts()}
        if username in accounts:
            return self.manager.create_binding(accounts[username]['account_id'], transport, provider_url, model_id, api_key_ref)
        return None

    def list_identities(self):
        return self.manager.list_accounts()

    def get_binding(self, username):
        accounts = {a['username']: a for a in self.manager.list_accounts()}
        if username in accounts:
            bindings = self.manager.get_bindings(accounts[username]['account_id'])
            if bindings:
                b = bindings[0]
                # Convert back to old transport key
                b['transport'] = b['provider_kind']
                return b
        return None
