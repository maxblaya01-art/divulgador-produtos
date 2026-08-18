[app]
title = Divulgador de Produtos
package.name = divulgadorprodutos
package.domain = br.tecnologiastore
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt
version = 1.0
requirements = python3,kivy,requests,beautifulsoup4,pillow,pyjnius
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
