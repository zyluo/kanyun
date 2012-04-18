#76 instance-0000004c 10.210.228.32
virsh list
if [ -z $instance_id ] 
then
	echo -e "instance_id:\c"
	read instance_id
fi
if [ -z $instance_ip ] 
then
	echo -e "instance_ip:\c"
	read instance_ip
fi
if [ -z $public_interface ] 
then
	echo -e "public_interface:\c"
	read public_interface
fi
sudo iptables -t filter -N nova-compute-f-inst-$instance_id
sudo iptables -I FORWARD -s $instance_ip -j nova-compute-f-inst-$instance_id
sudo iptables -A nova-compute-f-inst-$instance_id -o $public_interface \
                     -m comment \
                     --comment " $instance_id $instance_ip accounting rule "

sudo iptables-save -t filter -c|grep comment
