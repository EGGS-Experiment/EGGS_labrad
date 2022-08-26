#!/bin/sh
echo $LABRADHOST
echo $LABRADPORT
if [ -z "$PROG_HOME" ] ; then
  echo $PROG_HOME
  ## resolve links - $0 may be a link to PROG_HOME
  PRG="$0"
  echo $PRG
  # need this for relative symlinks
  while [ -h "$PRG" ] ; do
    ls=`ls -ld "$PRG"`
    link=`expr "$ls" : '.*-> \(.*\)$'`
    if expr "$link" : '/.*' > /dev/null; then
      PRG="$link"
    else
      PRG="`dirname "$PRG"`/$link"
    fi
    echo $PRG

  done
  echo $PRG

  saveddir=`pwd`

  PROG_HOME=`dirname "$PRG"`/..

  # make it fully qualified
  PROG_HOME=`cd "$PROG_HOME" && pwd`

  cd "$saveddir"
  echo $PRG

fi

echo $PRG

cygwin=false
mingw=false
darwin=false
case "`uname`" in
  CYGWIN*) cygwin=true
          ;;
  MINGW*) mingw=true
          ;;
  Darwin*) darwin=true
           if [ -z "$JAVA_VERSION" ] ; then
             JAVA_VERSION="CurrentJDK"
           else
            echo "Using Java version: $JAVA_VERSION" 1>&2
           fi
           if [ -z "$JAVA_HOME" ] ; then
             JAVA_HOME=/System/Library/Frameworks/JavaVM.framework/Versions/${JAVA_VERSION}/Home
           fi
           JVM_OPT="$JVM_OPT -Xdock:name=${PROG_NAME} -Xdock:icon=$PROG_HOME/icon-mac.png -Dapple.laf.useScreenMenuBar=true"
           JAVACMD="`which java`"
           ;;
esac

# Resolve JAVA_HOME from javac command path
if [ -z "$JAVA_HOME" ]; then
  javaExecutable="`which javac`"
  if [ -n "$javaExecutable" -a ! "`expr \"$javaExecutable\" : '\([^ ]*\)'`" = "no" ]; then
    # readlink(1) is not available as standard on Solaris 10.
    readLink=`which readlink`
    if [ ! `expr "$readLink" : '\([^ ]*\)'` = "no" ]; then
      javaExecutable="`readlink -f \"$javaExecutable\"`"
      javaHome="`dirname \"$javaExecutable\"`"
      javaHome=`expr "$javaHome" : '\(.*\)/bin'`
      JAVA_HOME="$javaHome"
      export JAVA_HOME
    fi
  fi
fi


if [ -z "$JAVACMD" ] ; then
  if [ -n "$JAVA_HOME"  ] ; then
    if [ -x "$JAVA_HOME/jre/sh/java" ] ; then
      # IBM's JDK on AIX uses strange locations for the executables
      JAVACMD="$JAVA_HOME/jre/sh/java"
    else
      JAVACMD="$JAVA_HOME/bin/java"
    fi
  else
    JAVACMD="`which java`"
  fi
fi

if [ ! -x "$JAVACMD" ] ; then
  echo "Error: JAVA_HOME is not defined correctly."
  echo "  We cannot execute $JAVACMD"
  exit 1
fi

if [ -z "$JAVA_HOME" ] ; then
  echo "Warning: JAVA_HOME environment variable is not set."
fi

CLASSPATH_SUFFIX=""
# Path separator used in EXTRA_CLASSPATH
PSEP=":"


PROG_NAME=labrad
PROG_VERSION=0.8.3

exec "$JAVACMD" \
     ${JVM_OPT} \
      \
     -cp "${PROG_HOME}/bin/lib/*${CLASSPATH_SUFFIX}" \
     -Dprog.home="${PROG_HOME}" \
     -Dprog.version="${PROG_VERSION}" \
     org.labrad.manager.Manager "$@"


