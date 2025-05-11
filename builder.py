import os, zipfile, subprocess
from uuid import uuid4

def extract_zip(zip_path, target_folder):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(target_folder)

def run_user_code(code, extracted_folder):
    # Insert extracted_folder into PYTHONPATH
    import sys
    sys.path.insert(0, os.path.abspath(extracted_folder))
    # Execute user code safely
    try:
        exec_globals = {}
        exec(code, exec_globals)
        return 'Code executed successfully.'
    except Exception as e:
        return f'Execution error: {e}'

def build_ipa():
    # Requires Xcode command-line tools and environment variables:
    # CERT_NAME: name of iOS code signing certificate in keychain
    # PROVISIONING_PROFILE: path to provisioning profile (.mobileprovision)
    bundle_id = os.getenv('APP_BUNDLE_ID')
    cert_name = os.getenv('CERT_NAME')
    profile = os.getenv('PROVISIONING_PROFILE')
    if not all([bundle_id, cert_name, profile]):
        raise EnvironmentError('APP_BUNDLE_ID, CERT_NAME, and PROVISIONING_PROFILE must be set.')
    build_dir = 'build_' + uuid4().hex
    os.makedirs(build_dir, exist_ok=True)
    # Assume there is an Xcode project in extracted folder
    archive_path = os.path.join(build_dir, 'app.xcarchive')
    # Archive
    subprocess.check_call([
        'xcodebuild', '-project', 'extracted/MyApp.xcodeproj',
        '-scheme', 'MyApp', 'archive',
        '-archivePath', archive_path,
        'CODE_SIGN_IDENTITY=' + cert_name,
        'PROVISIONING_PROFILE=' + profile
    ])
    # Export IPA
    export_path = os.path.join(build_dir, 'ipa')
    subprocess.check_call([
        'xcodebuild', '-exportArchive',
        '-archivePath', archive_path,
        '-exportOptionsPlist', 'ExportOptions.plist',
        '-exportPath', export_path
    ])
    ipa_file = [f for f in os.listdir(export_path) if f.endswith('.ipa')][0]
    ipa_path = os.path.join(export_path, ipa_file)
    # Generate manifest plist for OTA
    manifest = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
  <key>items</key>
  <array>
    <dict>
      <key>assets</key>
      <array>
        <dict>
          <key>kind</key>
          <string>software-package</string>
          <key>url</key>
          <string>https://{os.getenv('HOSTNAME')}:8000/{ipa_file}</string>
        </dict>
      </array>
      <key>metadata</key>
      <dict>
        <key>bundle-identifier</key>
        <string>{bundle_id}</string>
        <key>bundle-version</key>
        <string>1.0</string>
        <key>kind</key>
        <string>software</string>
        <key>title</key>
        <string>PyProgramzApp</string>
      </dict>
    </dict>
  </array>
</dict>
</plist>"""
    manifest_path = os.path.join(export_path, 'manifest.plist')
    with open(manifest_path, 'w') as f:
        f.write(manifest)
    # Return relative IPA and manifest URL for OTA
    return ipa_path, f"itms-services://?action=download-manifest&url=https://{os.getenv('HOSTNAME')}:8000/ipa/manifest.plist"

