if [ "$1" == "-a" ]; then
    arch_command="arch -arm64"
    shift  # Remove the '-a' option from the arguments
else
    arch_command=""
fi


$arch_command brew tap mongodb/brew
$arch_command brew install mongodb-database-tools

