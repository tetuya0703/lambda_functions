package=$1
if [ -z "$package" ]; then
  echo "need python file"
  exit 1
fi

mkdir python \
  && cp $package python \
  && zip -r sg.zip ./python \
  && mv sg.zip ~/Downloads \
  && rm -rf python
