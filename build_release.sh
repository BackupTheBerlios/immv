#!/bin/sh

if [ -z "$1" ]; then
  echo "Please specify the version number."
  exit 1
fi

echo "Remember that you have to tag the release in advance!"

fakeroot ./debian/rules clean


VERSION=$1
BUILD_PATH=$(mktemp -d)
RELEASE_DIR=$BUILD_PATH/immv-$VERSION

RELEASE_FILES="immv.py immv.1 README TODO"

git archive --prefix=immv-$VERSION/ v$VERSION | gzip - > $BUILD_PATH/immv.tar.gz
pushd $BUILD_PATH
tar xzf immv.tar.gz
tar czf immv_$VERSION.orig.tar.gz immv-$VERSION --exclude .git --exclude debian

cd immv-$VERSION
#fakeroot ./debian/rules build
debuild-pbuilder

PACKAGE_DIR=../package_dir
mkdir -p $PACKAGE_DIR/immv-$VERSION
cp $RELEASE_FILES $PACKAGE_DIR/immv-$VERSION
cd $PACKAGE_DIR
tar czf ../immv-$VERSION.tar.gz immv-$VERSION


echo
echo "Packages were created in "$BUILD_PATH
echo
echo $BUILD_PATH"/immv-"$VERSION.tar.gz
ls $BUILD_PATH/*.deb
echo
echo "Please upload them to Berlios and upload the contents of the www"
echo "directory to the Berlios FTP."
