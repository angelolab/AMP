STAGING_DIR="./to_dmg"
DMG_TMP="AMP-temp.dmg"
DMG_FINAL="AMP.dmg"

mkdir "${STAGING_DIR}"
cp -r dist/AMP.app "${STAGING_DIR}/."

hdiutil create "${DMG_TMP}" -volname "AMP" -srcfolder "${STAGING_DIR}" -size 1g -format UDRW

DEVICE=$(hdiutil attach -readwrite -noverify "${DMG_TMP}" | \
    egrep '^/dev/' | sed 1q | awk '{print $1}')

sleep 2

# add a link to the Applications dir
echo "Add link to /Applications"
pushd /Volumes/AMP
ln -s /Applications
popd
 
# tell the Finder to resize the window, set the background,
#  change the icon size, place the icons in the right position, etc.
echo '
   tell application "Finder"
     tell disk "AMP"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {400, 100, 920, 440}
           set viewOptions to the icon view options of container window
           set arrangement of viewOptions to not arranged
           set icon size of viewOptions to 72
           set position of item "AMP.app" of container window to {160, 205}
           set position of item "Applications" of container window to {360, 205}
           close
           open
           update without registering applications
           delay 2
     end tell
   end tell
' | osascript

sync

# unmount it
hdiutil detach "${DEVICE}"
 
# now make the final image a compressed disk image
echo "Creating compressed image"
hdiutil convert "${DMG_TMP}" -format UDZO -imagekey zlib-level=9 -o "${DMG_FINAL}"
 
# clean up
rm -rf "${DMG_TMP}"
rm -rf "${STAGING_DIR}"
 
echo 'Done.'
 
exit