"""Verification des mises a jour via GitHub releases"""
import json
import threading
import urllib.request
import urllib.error
from typing import Callable, Optional, Tuple


class UpdateChecker:
    """Verifie les mises a jour sur GitHub releases"""

    def __init__(self, current_version: str, github_repo: str):
        self.current_version = current_version
        self.github_repo = github_repo
        self.latest_version: Optional[str] = None
        self.download_url: Optional[str] = None
        self.has_update = False
        self._checked = False

    def check_async(self, callback: Callable[[bool, Optional[str], Optional[str]], None]) -> None:
        """Verifie les mises a jour dans un thread separé

        callback(has_update, latest_version, download_url)
        """
        thread = threading.Thread(
            target=self._check_and_callback,
            args=(callback,),
            daemon=True
        )
        thread.start()

    def _check_and_callback(self, callback: Callable) -> None:
        """Execute la verification et appelle le callback"""
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "OpenWhisper-UpdateChecker"}
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            self.latest_version = data.get("tag_name", "").lstrip("v")
            self.download_url = data.get("html_url", "")
            self._checked = True

            if self.latest_version and self.current_version:
                self.has_update = self._compare_versions(
                    self.latest_version,
                    self.current_version
                ) > 0

            print(f"[Update] Version actuelle: {self.current_version}")
            print(f"[Update] Derniere version: {self.latest_version}")
            print(f"[Update] Mise a jour disponible: {self.has_update}")

            callback(self.has_update, self.latest_version, self.download_url)

        except urllib.error.URLError as e:
            print(f"[Update] Erreur reseau: {e}")
            callback(False, None, None)
        except Exception as e:
            print(f"[Update] Erreur verification: {e}")
            callback(False, None, None)

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare deux versions semantiques

        Retourne:
            1 si v1 > v2
            0 si v1 == v2
           -1 si v1 < v2
        """
        def parse(v: str) -> Tuple[int, ...]:
            # Nettoyer la version (enlever prefixes comme 'v')
            v = v.lstrip("v")
            # Extraire seulement les chiffres
            parts = []
            for part in v.split("."):
                # Garder seulement la partie numerique
                num = ""
                for c in part:
                    if c.isdigit():
                        num += c
                    else:
                        break
                if num:
                    parts.append(int(num))
            return tuple(parts) if parts else (0,)

        parts1 = parse(v1)
        parts2 = parse(v2)

        # Padding pour longueur egale
        max_len = max(len(parts1), len(parts2))
        parts1 = parts1 + (0,) * (max_len - len(parts1))
        parts2 = parts2 + (0,) * (max_len - len(parts2))

        for a, b in zip(parts1, parts2):
            if a > b:
                return 1
            if a < b:
                return -1
        return 0
