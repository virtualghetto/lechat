#!/usr/bin/perl

=pod
Note: This is a modified version from "Friendly Script Updater".
/####################################################################
#                                                                   #
#    #      #####        ####  #   #   ###   #####      /\_/\       #
#    #      #           #      #   #  #   #    #       ( o.o )      #
#    #      ###         #      #####  #####    #        > ^ <       #
#    #      #           #      #   #  #   #    #        v1.20       #
#    #####  #####        ####  #   #  #   #    #       2015-07      #
#                                                                   #
#  Installation instructions:                                       #
#                                                                   #
#  Upload this file into your cgi-bin directory (you can rename it  #
#  to whatever  you want,  if you prefer)  and make it  executable  #
#  (chmod 711).  If you have language data or backups  you want to  #
#  restore initially,  you can copy that all into a textfile named  #
#  "lechat.txt" and put it next to your script file on the server.  #
#  Then call the script in your browser with parameter like this:   #
#                                                                   #
#  http://(server)/(cgi-path)/(script-name).cgi?action=setup        #
#                                                                   #
#  All necessary installation settings can be made from there.      #
#  The server needs to support Perl CGI scripts, obviously. If you  #
#  have trouble,  make sure the file is uploaded in ASCII-mode and  #
#  Perl scripts are allowed to create files and folders.            #
#  Banner killers for some known hosts are built in, please report  #
#  back any problems there or any other hosts you want added!       #
#                                                                   #
#  If you make translations and want to share them, please send me  #
#  a copy of the backup data for my website, thanks!  All text can  #
#  be edited conveniently as superuser on the setup page.           #
#                                                                   #
#  This script comes  without any  warranties.  Use it at your own  #
#  risk, don't  blame me for any modifications you make. Verify my  #
#  attached  PGP-signature, to make sure  you got the original and  #
#  not an altered copy! Really, do verify it!                       #
#  If you spread the script,  please only give  away the original,  #
#  or better, just refer to: http://4fvfamdpoulu2nms.onion/lechat/  #
#                                                                   #
#  If you add your own cool features and want to share with others, #
#  feel free,  but please  modify at least the version tag and add  #
#  your name to it, so it is clear that it is not my original code  #
#  anymore.  If you send  me a copy of your edited script, I might  #
#  use some of your ideas in future versions. Thank you!            #
#                                                                   #
#  I wrote the script from scratch and all the code is my own, but  #
#  as you may notice,  I took some ideas  from other scripts  that  #
#  are out there. Bug reports and feedback are very welcome.        #
#                                                                   #
#  The "LE" in the name  you can take as  "Lucky Eddie", or  since  #
#  the script was  meant to be lean  and easy on server resources,  #
#  as "Light Edition". It may even be the french word for "the" if  #
#  you prefer. Translated from french to english, "le chat" means:  #
#  "the cat".                                                       #
#                                                                   #
#  Other than that, enjoy! ;)                                       #
#                                                                   #
#  Lucky Eddie                                                      #
#                                                                   #
#  Edit: This is a revision of the script added features are:       #
#  -Added in-line moderation:                                       #
#      -"/kick [message]:[user]" //Kick [user] with the [message]   #
#      -"/delmess [user]" //Deletes all users messages              #
#      -"/clean room" //Clears the rooms messages                   #
#      -"/logout [user]" //Logs out [user]                          #
#      -"/name [user]" // Adds user to banned name list.            #
#                                                                   #
#  - Fixed some html errors to make the script a tad bit faster     #
#  - Centered everything for continuity.                            #
#  - When the user presses delete all it will ask for comfirmation  #
#  - Added Links                                                    #
#      -The /[command] only works when the user is admin or mod     #
#                                                                   #
#  - Added Link Shortener                                           #
#  - Updated Rules & Help                                           #
#      -Included in-line moderation changes explaination            #
#      -Added list of included emojis                               #
#                                                                   #
#  - Name fliter intergration to block unwanted names               #
#      -When using the /name command it adds the name to a list     #
#      -Before someone gains access to the chat it checks the name  #
#      -Full number names are also blocked.                         #
#                                                                   #
####################################################################/
=cut

use strict;
use warnings;
use Fcntl qw(:DEFAULT :flock);

######################################################################
# Data directory, could be changed, but shouldn't be necessary.
######################################################################
my $datadir='./lcdat';

######################################################################
# No need to change anything below. Always use: *.cgi?action=setup
######################################################################
my($version,$lastchanged)=('v1.20 FSU','2015-07');
my($S,%Q)=(&GetScript,&GetQuery,&GetParam);
my %T;# Test flags
my %U;# this User data
my %P;# all Present users (nick=>[hex,status,style])
my %A;# All registered members (nick=>[hex,status,style])
my @M;# Members: display names
my @G;# Guests: display names
my %F;# Fonts
my %I;# Internal texts and error messages
my %L;# Language editing
my %C;# Configuration
my %H;# HTML-stuff
load_config();

######################################################################
# main program: decide what to do based on queries
######################################################################
if($Q{action}[0]eq'setup'){
	send_init() unless -e"$datadir/admin";
	send_alogin() unless valid_admin($Q{nick}[0],$Q{pass}[0],$Q{hexpass}[0]);
	if($Q{do}[0]eq'config'){
		set_config();
		save_config();
	}elsif($Q{do}[0]eq'chataccess'){ 
		set_chat_access($Q{set}[0]);
	}elsif($Q{do}[0]eq'backup'){
		$I{backdat}=get_backup($Q{what}[0]);
	}elsif($Q{do}[0]eq'restore'){
		$I{backdat}=get_restore_results();
	}elsif($Q{do}[0]eq'mainadmin'and$U{status}==9){
		send_setup(change_admin_status());
	}elsif($Q{do}[0]eq'resetlanguage'and$U{status}==9){
		delete_file('language');
		load_config();
	}
	send_setup();
}
elsif($Q{action}[0]eq'init' and !-e"$datadir/admin"){
	init_chat();
}
elsif($Q{action}[0]eq'language'){
	send_alogin() unless valid_admin($Q{nick}[0],$Q{pass}[0],$Q{hexpass}[0])==2;
	save_langedit()if$Q{do}[0]eq'save';
	$I{backdat}=get_restore_results('langedit')if$Q{do}[0]eq'restore';
	load_langedit();
	$I{backdat}=get_backup('langedit')if$Q{do}[0]eq'backup';
	send_language();
}
elsif($T{access}==0){
	send_suspended();
}
elsif($Q{action}[0]eq'redirect'){
	send_redirect($Q{url}[0]);
}
elsif($T{access}!=1){
	send_suspended();
}
elsif($Q{action}[0]eq'wait'){
	check_waiting_session();
	send_waiting_room();
}
elsif($Q{action}[0]eq'view'){
	check_session();
	send_messages();
}
elsif($Q{action}[0]eq'post'){
	if($Q{message}[0]=~/^\s*$/){
		check_session()
	}
	else{
		update_session();
		validate_input();
		if($U{status}>=6 and $U{message}=~m/^\//){
			send_command();
		}
		else{
			add_message() unless $U{autokick}==3;
		}
		del_all_messages() if $U{autokick}==3;
		kick_chatter($U{nickname},$U{kickmessage}) if $U{autokick} and $U{status}<6;
		if($U{autokick} and $U{status}>=6){
			$U{message}="$I{kickfilter}";
			$U{message}.=" ($U{kickmessage})" if $U{kickmessage};
			add_staff_message();
		}
	}
	send_post();
}
elsif($Q{action}[0]eq'delete'){
	check_session();
	del_all_messages() if $Q{what}[0]eq'all';
	del_last_message() if $Q{what}[0]eq'last';
	if ($Q{what}[0] eq 'check'){
	send_check();
	}
	else{send_post();}
}
elsif($Q{action}[0]eq'login'){
	create_session();
	send_frameset();
}
elsif($Q{action}[0]eq'upload'){
	check_session();
	
}
elsif($Q{action}[0]eq'controls'){
	check_session();
	send_controls();
}
elsif($Q{action}[0]eq'profile'){
	if($Q{do}[0]eq'save'){save_profile()}else{check_session()}
	send_profile();
}
elsif($Q{action}[0]eq'entry'){
	check_session();
	send_entry();
}
elsif($Q{action}[0]eq'logout'){
	kill_session();
	send_logout();
}
elsif($Q{action}[0]eq'colours'){
	check_session();
	send_colours();
}
elsif($Q{action}[0]eq'help'){
	check_session();
	send_help();
}
elsif($Q{action}[0]eq'links'){
	send_links() && check_session() if $C{linksswitch}==1;
}
elsif($Q{action}[0]eq'admin'){
	check_session();
	send_login() unless $U{status}>=6;
	if($Q{do}[0]eq'clean'){
		send_choose_messages() if $Q{what}[0]eq'choose';
		clean_selected() if $Q{what}[0]eq'selected';
		clean_room() if $Q{what}[0]eq'room';
		send_messages();
	}
	elsif($Q{do}[0]eq'kick'){
		send_admin() if $Q{name}[0]eq'bla';
		unless(kick_chatter(pack('H*',$Q{name}[0]),$Q{kickmessage}[0])){
			$I{errcantkick}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
			send_admin($I{errcantkick});
		}
		del_all_messages(pack('H*',$Q{name}[0])) if $Q{what}[0]eq'purge';
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'logout'){
		send_admin() if $Q{name}[0]eq'';
		unless(logout_chatter(pack('H*',$Q{name}[0]))){
			$I{errcantlogout}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
			send_admin($I{errcantlogout}); 
		}
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'sessions'){
		send_sessions();
	}
	elsif($Q{do}[0]eq'guests'){
		set_guests_access($Q{set}[0]) if($U{status}>=7 or $Q{set}[0]==0);
	}
	elsif($Q{do}[0]eq'register'){
		register_guest();
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'status'){
		change_status();
	}
	elsif($Q{do}[0]eq'regnew'){
		register_new();
	}
	elsif($Q{do}[0]eq'newcomers' and $U{status}>=7){
		edit_waiting_sessions($Q{what}[0]);
		send_waiting_admin();
	}
	send_admin();
}
else{
	send_login();
}
exit;

######################################################################
# html output subs
######################################################################

sub print_headers{print "Content-Type: text/html; charset=$H{encoding}\nContent-Language: $I{languagecode}\nPragma: no-cache\nExpires: 0\n"}
sub print_stylesheet{print qq|\n<style type="text/css"><!--\n$C{cssglobal}\n|,$C{'css'.$_[0]},"\n$H{add_css}--></style>\n";}
sub print_end{print $H{end_body},$H{end_html};exit}
sub frmpst{"<$H{form}>".hidden('action',$_[0]).hidden('session',$U{session}).($_[1]?hidden('what',$_[1]).hidden('sendto',$Q{sendto}[0]).hidden('multi',$Q{multi}[0]):'')}
sub frmlng{"<$H{form}>".hidden('action','language').hidden('nick',$Q{nick}[0]).hidden('hexpass',$Q{hexpass}[0]||unpack('H*',$Q{pass}[0])).($_[0]?hidden('do',$_[0]):'')}
sub frmset{"<$H{form}>".hidden('action','setup').hidden('nick',$Q{nick}[0]).hidden('hexpass',$Q{hexpass}[0]||unpack('H*',$Q{pass}[0])).($_[0]?hidden('do',$_[0]):'').($_[1]?hidden('what',$_[1]):'')}
sub frmadm{"<$H{form}>".hidden('action','admin').hidden('do',$_[0]).hidden('session',$U{session})}
sub hidden{qq|<input type="hidden" name="$_[0]" value="$_[1]">|}
sub submit{qq|<input type="submit" value="$_[0]"$_[1]>|}
sub thr{'<tr><td'.($_[0]?qq| colspan="$_[0]"|:'').'><hr></td></tr>'}
sub cfgyn{qq|<tr><td align="left">$I{$_[0]}</td><td align="right"><input type="radio" name="$_[0]" id="$_[0]1" value="1"|.($C{$_[0]}?' checked':'').qq|><label for="$_[0]1">&nbsp;$I{yes}</label>&nbsp;&nbsp;&nbsp;<input type="radio" name="$_[0]" id="$_[0]0" value="0"|.($C{$_[0]}?'':' checked').qq|><label for="$_[0]0">&nbsp;$I{no}</label></td></tr>|}
sub cfgta{qq|<tr><td align="left" valign="top">$I{$_[0]}</td><td align="right"><textarea name="$_[0]" rows="4" cols="40" wrap="off">$C{$_[0]}</textarea></td></tr>|}
sub cfgt{qq|<tr><td align="left">$I{$_[0]}</td><td align="right"><input type="text" name="$_[0]" value="$C{$_[0]}" size="$_[1]"|.($_[2]?qq| maxlength="$_[2]"|:'').qq|></td></tr>|}
sub cfgts{cfgt($_[0],'7','6')}
sub cfgtm{cfgt($_[0],'30')}
sub cfgtb{cfgt($_[0],'50')}

sub print_start{my($css,$ref,$url)=@_;
	$url=~s/&amp;/&/g if$url;# Don't escape "&" in URLs here, it breaks some (older) browsers!
	print_headers();
	print "Refresh: $ref; URL=$url\n"if$url;
	print "$H{begin_html}<head>$H{meta_html}";
	print qq|\n<meta http-equiv="Refresh" content="$ref; URL=$url">|if$url;
	print_stylesheet($css);
	print '</head>',$H{begin_body};
}

sub linkrel{
	return unless $_[0];
	my($itype)=($_[0]=~/(?:data:image\/|\.)(x-icon|ico|gif|png)(?:;|$)/);
	$itype='x-icon'if'ico'eq$itype;
	$itype=qq| type="image/$itype"|if$itype;
	return qq|<link rel="shortcut icon" href="$_[0]"$itype>\n|;
}

sub send_redirect{my $href=$_[0];
	# Link redirection to strip off referers and prevent session leakage.
	if($T{access}==1 and (!$C{createlinks} or $C{useextderef})){
		print_start('error');
		print "<h2>$I{errnolinks}</h2>";
		print_end();
	}
	# check for protocol, assume http if none given and correct the link accordingly.
	my ($scheme)=$href=~m~^([\w]*://|mailto:)~;
	if($scheme eq ''){$scheme='http://';$href=$scheme.$href}
	# Only do automatic refresh on http, else just give links
	if($scheme eq 'http://'){
		print_start('view',0,$href);
		print qq|<center><h2>$I{linkredirect}</h2><a href="$href">$_[0]</a></center>|;
	}else{
		$href=~s~^([\w]*://)?~http://~;
		print_start('view');
		print qq|<center><h2>$I{linknonhttp}</h2><a href="$_[0]">$_[0]</a><h2>$I{linktryhttp}</h2><a href="$href">$href</a></center>|;
	}
	print_end();
}

sub send_alogin{
	print_start('admin');
	print qq|<center><$H{form}>|,hidden('action','setup'),qq|<table><tr><td align="left">$I{aloginname}</td><td><input type="text" name="nick" size="25"></td></tr><tr><td align="left">$I{aloginpass}</td><td><input type="password" name="pass" size="25"></td></tr><tr><td colspan="2" align="right">|,submit($I{aloginbut}),qq|</td></tr></table></form></center>|;
	print_end();
}

sub send_language{
	print_start('admin');
	print qq|<center><h1>$I{lngheader}</h1><br><table cellspacing="0"><tr><td align="left"><table cellspacing="0"><tr><td>|,frmlng('backup'),submit($I{lngbackup}),qq|</form></td><td>&nbsp;&dArr;</td></tr></table></td></tr><tr><td>|,frmlng('restore'),qq|<table cellspacing="0"><tr><td><textarea name="backupdata" rows="8" cols="80" wrap="off">$I{backdat}\n</textarea></td></tr><tr><td align="right"><table cellspacing="0"><tr><td>&nbsp;&rArr;</td><td>|,submit($I{lngload}),qq|</td></tr></table></td></tr></table></form></td></table><br>|,frmlng('save'),qq|<table cellspacing="0" cellpadding="5" width="1"><tr><td colspan="2" align="left">$I{lnghelp}</td></tr><tr><td align="left"><h2>$I{lngtoken}</h2></td><td align="left"><h2>$I{lngdeftxt}</h2></td></tr><tr><td colspan=2 align="left"><hr></td></tr>|;
	my $start=tell(DATA);
	while(<DATA>){
		if($_=~/^#/){
			my ($sect)=$_=~/^#\s*(.+)/;
			print qq|<tr><td colspan="2" align="left"><hr></td></tr><tr><td colspan="2" align="left"><h3>$sect</h3></td></tr>|;
		}else{
			my($ikey,$ival)=$_=~/^([a-z_]+)\s*=(.+)/i;
			if($ikey and 'stop_action'ne$ikey){
				$I{$ikey}=$ival;
				my $rows=int(length($ival)/75)+1;
				$ival=formsafe($ival);
				$L{$ikey}=formsafe($L{$ikey});
				my $iinp=qq|<textarea rows="$rows" cols="75" name="$ikey" wrap="virtual">$L{$ikey}</textarea>|;
				print qq|<tr><td valign="top" align="left">$ikey</td><td valign="top" align="left">$ival<br>$iinp</td></tr>|;
			}
		}
	}
	seek(DATA,$start,0);
	print qq|<tr><td colspan="2" align="left"><hr></td></tr><tr><td colspan="2" align="center">|,submit($I{savechanges}),qq|</td></tr></table></form><br>$H{backtosetup}<br>$H{versiontag}</center>|;
	print_end();
}

sub send_check{
	$U{postid}=substr($^T,-6);
	print_start('post');
	print '<center><table cellspacing="4"><tr><td valign="top">Are you sure you want to delete all your messages?</td><td valign="top"></td>';
	print '</select></td></tr></table></form></td></tr><tr><td height="4"></td></tr><tr><td align="center"><table cellspacing="10"><tr><td>',frmpst('delete','last'),submit($I{butdellast},qq| style="$C{styledellast}"|),'</form></td><td>',frmpst('delete','all'),submit($I{butdelall},qq| style="$C{styledelall}"|),'</form><td>';
	print '</tr></table></td></tr></table></center>';
	print_end();
}

sub send_setup{
	read_members()if($U{status}==9);
	print_start('admin');
	$I{nickhelp}=~s/<MAX>/$C{maxname}/;
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	foreach(keys %C){next if $_ eq 'textfilters';$C{$_}=formsafe($C{$_})}
	print qq|<center><h2>$I{chatsetup}</h2>|,frmset('chataccess'),qq|<table cellspacing="0"><tr><td><b>$I{chataccess}</b></td><td>&nbsp;</td><td><input type="radio" name="set" id="off" value="0"|,$T{access}==0?' checked':'',qq|></td><td><label for="off">$I{suspend}</label></td><td>&nbsp;</td><td><input type="radio" name="set" id="on" value="1"|,$T{access}==1?' checked':'',qq|></td><td><label for="on">$I{enabled}</label></td><td>&nbsp;</td><td><input type="radio" name="set" id="deref" value="2"|,$T{access}==2?' checked':'',qq|></td><td><label for="deref">$I{derefonly}</label></td><td>&nbsp;</td><td>|,submit($I{butset}),qq|</td></table></form><br><h2>$I{backups}</h2><table cellspacing="0"><tr><td align="left"><table cellspacing="0"><tr><td>|;
	print frmset('backup','members'),submit($I{backmem}),qq|</form></td><td>&dArr;&nbsp;</td><td>|,frmset('backup','config'),submit($I{backcfg}),qq|</form></td><td>&dArr;&nbsp;</td></tr></table></td></tr><tr><td>|,frmset('restore'),qq|<table cellspacing="0"><tr><td><textarea name="backupdata" rows="8" cols="80" wrap="off">$I{backdat}\n</textarea></td></tr><tr><td align="right"><table cellspacing="0"><tr><td>&nbsp;&rArr;</td><td>|,submit($I{restore}),qq|</td></tr></table></td></tr></table></form></td></tr></table><br>|;
	if($U{status}==9){
		print qq|<h2>$I{mainadmins}</h2><i>$_[0]</i><table cellspacing="0">|,thr(),qq|<tr><td align="left"><b>$I{regadmin}</b></td></tr><tr><td align="right">|,frmset('mainadmin','new'),qq|<table cellspacing="0"><tr title="$I{nickhelp}"><td>&nbsp;</td><td align="left">$I{nickname}</td><td><input type="text" name="admnick" size="20"></td><td>&nbsp;</td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{password}</td><td><input type="text" name="admpass" size="20"></td><td>|,submit($I{butregadmin}),qq|</td></tr></table></form></td></tr>|,thr(),qq|<tr><td align="left"><b>$I{raiseadmin}</b></td></tr><tr><td align="right">|,frmset('mainadmin','up'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td><select name="admnick" size="1"><option value="">$I{selchoose}</option>|;
		print_memberslist(7);
		print qq|</select></td><td align="right">|,submit($I{butraise}),qq|</td></tr></table></form></td></tr>|,thr(),qq|<tr><td align="left"><b>$I{loweradmin}</b></td></tr><tr><td align="right">|,frmset('mainadmin','down'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td><select name="admnick" size="1"><option value="">$I{selchoose}</option>|;
		print_memberslist(8);
		print qq|</select></td><td>|,submit($I{butlower}),qq|</td></tr></table></form></td></tr>|,thr(),qq|</table><br><br><h2>$I{cfglanguage}</h2>|,frmlng(),submit($I{editlanguage}),qq|</form><br>|,frmset('resetlanguage'),submit($I{resetlanguage},-e"$datadir/language"?'':' disabled'),qq|</form><br><h2>$I{cfgsettings}</h2>$I{cfgmainadm}<br><br>|;
	}else{
		print "<h2>$I{cfgsettings}</h2>",frmset('config'),'<table cellspacing="0">',thr(2),cfgyn('redirifsusp'),cfgtm('redirtourl'),thr(2),cfgyn('allowfonts'),cfgyn('allowmultiline'),cfgyn('allowpms'),cfgyn('rndguestcol'),thr(2),cfgyn('createlinks'),cfgyn('useextderef'),cfgtm('extderefurl'),thr(2);
		print_filters();
		print thr(2),cfgts('sessionexpire'),cfgts('guestsexpire'),cfgts('messageexpire'),cfgts('kickpenalty'),cfgts('waitingexpire'),thr(2),cfgts('defaultrefresh'),cfgts('minrefresh'),cfgts('maxrefresh'),cfgts('floodlimit'),thr(2),
			cfgts('boxwidthdef'),cfgts('boxheightdef'),cfgts('maxmessage'),cfgts('maxname'),cfgts('minpass'),thr(2),cfgtm('title'),cfgtm('favicon'),cfgtm('noguests'),cfgtm('loginbutton'),thr(2),cfgta('header'),cfgta('footer'),thr(2),cfgta('rulestxt'),cfgta('links'),cfgyn('linksswitch'),thr(2),cfgtb('nowchatting'),thr(2),cfgtb('entrymessage'),cfgtb('logoutmessage'),cfgtb('kickederror'),thr(2),
			cfgtb('roomentry'),cfgtb('roomexit'),cfgtb('regmessage'),cfgtb('kickedmessage'),cfgtb('roomclean'),thr(2),cfgtb('mesall'),cfgtb('mesmem'),cfgtb('messtaff'),cfgtb('mespm'),thr(2),cfgts('colbg'),cfgts('coltxt'),cfgts('collnk'),cfgts('colvis'),cfgts('colact'),thr(2),
			cfgta('cssglobal'),cfgtb('styleback'),thr(2),cfgta('csslogin'),cfgtb('stylelogintext'),cfgtb('stylecolselect'),cfgtb('styleenter'),thr(2),cfgta('csspost'),cfgtb('styleposttext'),cfgtb('stylepostsend'),cfgtb('stylesendlist'),cfgtb('styledellast'),cfgtb('styledelall'),cfgtb('styleswitch'),thr(2),
			cfgta('cssview'),cfgtb('styledelsome'),cfgtb('stylecheckwait'),thr(2),cfgta('csswait'),cfgtb('stylewaitrel'),thr(2),cfgta('csscontrols'),cfgtb('stylerelpost'),cfgtb('stylerelmes'),cfgtb('styleprofile'),cfgtb('styleadmin'),cfgtb('stylerules'),cfgtb('styleexit'),thr(2),
			cfgta('cssprofile'),thr(2),cfgta('cssrules'),thr(2),cfgta('cssadmin'),thr(2),cfgta('csserror'),thr(2),cfgtb('tableattributes'),cfgtb('frameattributes'),cfgtb('framesizes'),thr(2);
		print qq|<tr><td colspan="2" align="center"><small>$I{lastchanged} $C{lastchangedat}/$C{lastchangedby}</small><br><br></td></tr><tr><td colspan="2" align="center">|,submit($I{savechanges}),'</td></tr></table></form><br>';
	}
	print "<$H{form}>",hidden('action','setup'),submit($I{butlogout}),"</form><br>$H{versiontag}</center>";
	print_end();
}

sub send_admin{
	read_members();
	print_start('admin');
	$I{admkick}=~s/<KICK>/$C{kickpenalty}/;
	$I{nickhelp}=~s/<MAX>/$C{maxname}/;
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	my $chlist=qq|<select name="name" size="1"><option value="">$I{selchoose}</option>|;foreach(sort {lc($a) cmp lc($b)} keys %P){$chlist.=qq|<option value="$P{$_}[0]" style="$P{$_}[2]">$_</option>|if($P{$_}[1]>0 and $P{$_}[1]<$U{status})};$chlist.='</select>';
	my @gset;$gset[$T{guests}]=' checked';$gset[4]=' disabled'if$U{status}<7;
	print qq|<center><h2>$I{admheader}</h2><i>$_[0]</i><table cellspacing="0">|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admclean}</b></td><td align="right">|,frmadm('clean'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td><input type="radio" name="what" id="room" value="room"></td><td align="left"><label for="room">$I{admcleanall}</label></td><td>&nbsp;</td><td><input type="radio" name="what" id="choose" value="choose" checked></td><td align="left"><label for="choose">$I{admcleansome}</label></td><td>&nbsp;</td><td>|,submit($I{butadmclean}),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admkick}</b></td></tr><tr><td align="right">|,frmadm('kick'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td align="left" colspan="3">$I{admkickmes} <input type="text" name="kickmessage" size="45"></td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td align="left"><input type="checkbox" name="what" value="purge" id="purge" checked><label for="purge">&nbsp;$I{admkickpurge}</label></td><td>&nbsp;</td><td align="right">$chlist</td><td>|,submit($I{butadmkick}),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{adminactive}</b></td><td align="right">|,frmadm('logout'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td valign="bottom">$chlist</td><td valign="bottom">|,submit($I{butadminactive}),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admvsessions}</b></td><td align="right">|,frmadm('sessions'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td>|,submit($I{butadmview}),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admguests}</b></td></tr><tr><td align="right">|,frmadm('guests'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td><input type="radio" name="set" id="set0" value="0"$gset[0]></td><td align="left"><label for="set0">$I{admguestsoff}</label></td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td><input type="radio" name="set" id="set1" value="1"$gset[1]$gset[4]></td><td align="left"><label for="set1">$I{admguestson}</label></td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td><input type="radio" name="set" id="set2" value="2"$gset[2]$gset[4]></td><td align="left"><label for="set2">$I{admguestsauto}</label></td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td><input type="radio" name="set" id="set3" value="3"$gset[3]$gset[4]></td><td align="left"><label for="set3">$I{admguestsbell}</label></td><td>&nbsp;</td><td valign="bottom">|,submit($I{butadmset}),qq|</td></tr></table></form></table></td></tr>|,thr();
	if($U{status}>=7){
		print qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admregguest}</b></td><td align="right">|,frmadm('register'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td valign="bottom"><select name="name" size="1"><option value="">$I{selchoose}</option>|;
		foreach(sort {lc($a) cmp lc($b)} keys %P){print '<option value="',$P{$_}[0],'" style="',$P{$_}[2],'">',$_,'</option>'if $P{$_}[1]==1} 
		print qq|</select></td><td valign="bottom">|,submit($I{butadmreg}),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admmembers}</b></td></tr><tr><td align="right">|,frmadm('status'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td valign="bottom" align="right"><select name="name" size="1"><option value="">$I{selchoose}</option>|;
		print_memberslist();
		print qq|</select><select name="set" size="1"><option value="">$I{selchoose}</option><option value="-">$I{selmemdelete}</option><option value="0">$I{selmemdeny} $I{symdenied}</option><option value="2">$I{selmemreg}</option><option value="6">$I{selmemmod} $I{symmod}</option>|;
		print qq|<option value="7">$I{selmemadmin} $I{symadmin}</option>|if($U{status}==8);
		print qq|</select></td><td valign="bottom">|,submit($I{butadmstatus}),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admregnew}</b></td></tr><tr><td align="right">|,frmadm('regnew'),qq|<table cellspacing="0"><tr title="$I{nickhelp}"><td>&nbsp;</td><td align="left">$I{nickname}</td><td><input type="text" name="name" size="20"></td><td>&nbsp;</td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{password}</td><td><input type="text" name="pass" size="20"></td><td valign="bottom">|,submit($I{butadmregnew}),'</td></tr></table></form></td></tr></table></td></tr>',thr();
	}
	print qq|</table>$H{backtochat}</center>|;
	print_end();
}

sub send_sessions{
	my @lines=parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
	print_start('admin');
	print qq|<center><h1>$I{admsessions}</h1><table border="0" cellpadding="5">|;
	print qq|<thead valign="middle"><tr><th align="left"><b>$I{nicklist}</b></th><th align="center"><b>$I{timeoutin}</b></th><th align="center"><b>$I{ip}</b></th><th align="left"><b>$I{useragent}</b></th></tr></thead><tbody valign="middle">|;
	foreach(@lines){
		my %temp=sessionhash($_);
		my $s=$temp{status}==2?'':'&nbsp;'.($temp{status}==0?$I{symdenied}:$temp{status}==1?$I{symguest}:$temp{status}==6?$I{symmod}:$temp{status}>=7?$I{symadmin}:'');
		print '<tr><td align="left">',style_this($temp{nickname}.$s,$temp{fontinfo}),'</td><td align="center">'.get_timeout($temp{lastpost},$temp{status}),'</td><td align="center">',($U{status}>$temp{status}or$U{session}eq$temp{session})?qq|$temp{ip}</td><td align="left">$temp{useragent}|:'-</td><td align="left">-','</td></tr>';
	}
	print "</tbody></table><br>$H{backtochat}</center>";
	print_end();
}

sub send_suspended{
	print_start('error',0,$C{redirifsusp}?$C{redirtourl}:'');
	print "<h1>$I{suspended}</h1><p>",$C{redirifsusp}?qq|<a href="|.htmlsafe($C{redirtourl}).qq|">$I{redirtext}</a>|:$I{susptext},"</p><hr>";
	print_end();
}

sub send_frameset{
	print_headers();
	print "$H{begin_frames}<head>$H{meta_html}";
	print_stylesheet('view');
	print qq|</head>\n<frameset rows="$C{framesizes}" $C{frameattributes}><frame name="post" src="$S?action=post&amp;session=$U{session}"><frame name="view" src="$S?action=entry&amp;session=$U{session}"><frame name="controls" src="$S?action=controls&amp;session=$U{session}"><noframes>$H{begin_body}$I{frames}$H{backtologin}$H{end_body}</noframes></frameset>$H{end_html}|;
	exit;
}

sub send_messages{
	get_waiting_count()if($T{guests}==4 and $U{status}>=7);
	my $url="$S?action=view&amp;session=$U{session}&amp;nocache=";
	print_start('view',$U{refresh},$url.substr($^T,-6));
	print '<a name="top"></a>';
	print_chatters();
	# <a href="#bottom"> does not work in some older browsers, full URL is needed with anchors!
	print qq|<table cellspacing="0" width="100%"><tr><td valign="top" align="right"><a href="$url$Q{nocache}[0]#bottom">$I{navbot}</a></td></tr></table>|;
	print_messages();
	print qq|<a name="bottom"></a><table cellspacing="0" width="100%"><tr><td align=right><a href="$url$Q{nocache}[0]#top">$I{navtop}</a></td></tr></table>|;
	print_end();
}

sub send_choose_messages{
	print_start('view');
	print frmadm('clean'),hidden('what','selected'),submit($I{butdelsome},qq| style="$C{styledelsome}"|),'<br><br>';
	print_messages($U{status});
	print "</form><br>$H{backtochat}";
	print_end();
}

sub send_links{
	print_start('rules');
	unless($C{links}=~/<br>/i){$C{links}=~s/\r\n/<br>/g;$C{links}=~s/\n/<br>/g;$C{links}=~s/\r/<br>/g}
	print "$C{links}";
	print_end();
}

sub send_post{
	$U{postid}=substr($^T,-6);
	print_start('post');
	print qq|<center><table cellspacing="0"><tr><td align="center">|,frmpst('post'),hidden('postid',$U{postid}),$C{allowmultiline}?hidden('multi',$Q{multi}[0]):'';
	print qq|<table cellspacing="0"><tr><td valign="top">$U{displayname}</td><td valign="top">:</td>|;
	if($Q{multi}[0] and $C{allowmultiline}){print qq|<td valign="top"><textarea name="message" wrap="virtual" rows="$U{boxheight}" cols="$U{boxwidth}" style="$C{styleposttext};background-color:#$C{colbg};$U{style}">$U{rejected}</textarea></td>|}
	else{print qq|<td valign="top"><input type="text" name="message" value="$U{rejected}" size="$U{boxwidth}" maxlength="$C{maxmessage}" style="$C{styleposttext};background-color:#$C{colbg};$U{style}"></td>|}
	print qq|<td valign="top">|,submit($I{butsendto},qq| style="$C{stylepostsend}"|),qq|</td><td valign="top"><select name="sendto" size="1" style="$C{stylesendlist};background-color:#$C{colbg};color:#$C{coltxt}">|;
	print '<option ',$Q{sendto}[0]eq'*'?'selected ':'','value="*">-',$I{seltoall},'-</option>';
	print '<option ',$Q{sendto}[0]eq'?'?'selected ':'','value="?">-',$I{seltomem},'-</option>'if$U{status}>=2;
	print '<option ',$Q{sendto}[0]eq'#'?'selected ':'','value="#">-',$I{seltoadm},'-</option>'if$U{status}>=6;
	if($C{allowpms}){foreach(sort {lc($a) cmp lc($b)} keys %P){print '<option ',$Q{sendto}[0]eq$P{$_}[0]?'selected ':'',qq|value="$P{$_}[0]" style="$P{$_}[2]">$_</option>|unless$U{nickname}eq$_}}
	print '</select></td></tr></table></form></td></tr><tr><td height="8"></td></tr><tr><td align="center"><table cellspacing="5"><tr><td>',frmpst('delete','last'),submit($I{butdellast},qq| style="$C{styledellast}"|),'</form></td><td>',frmpst('delete','check'),submit($I{butdelall},qq| style="$C{styledelall}"|),'</form></td><td width="10"></td><td>';
	print frmpst('post'),hidden('sendto',$Q{sendto}[0]),hidden('multi',$Q{multi}[0]?'':'on'),submit($Q{multi}[0]?$I{butsingleline}:$I{butmultiline},qq| style="$C{styleswitch}"|),'</form></td>'if$C{allowmultiline};
	print '</tr></table></td></tr><td></td></table></center>';
	#<td>',frmpst('action','upload'),submit($I{butupload},qq| style="$C{styledelall}"|),'</form></td>
	print_end();
}

sub send_help{
	unless($C{rulestxt}=~/<br>/i){$C{rulestxt}=~s/\r\n/<br>/g;$C{rulestxt}=~s/\n/<br>/g;$C{rulestxt}=~s/\r/<br>/g}
	$C{rulestxt}=~s/<IP>/$ENV{REMOTE_ADDR}/g;
	print_start('rules');
	print "<h2>$I{rules}</h2>$C{rulestxt}<br><br><hr><h2>$I{help}</h2>",$U{status}>=0?"$I{helpguests}<br>":'',$U{status}>=2?"<br>$I{helpregs}<br>":'',$U{status}>=6?"<br>$I{helpmods}<br>":'',$U{status}>=7?"<br>$I{helpadmins}<br>":'',"<br><hr><center>$H{backtochat}<br>$H{versiontag}</center>";
	print_end();
}

sub send_profile{
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	$I{refreshrate}=~s/<MIN>/$C{minrefresh}/;
	$I{refreshrate}=~s/<MAX>/$C{maxrefresh}/;
	$I{entryrefresh}=~s/<DEFAULT>/$C{defaultrefresh}/;
	print_start('profile');
	print "<center><$H{form}>",hidden('action','profile'),hidden('do','save'),hidden('session',$U{session}),qq|<h2>$I{profileheader}</h2><i>$_[0]</i><table cellspacing="0">|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{refreshrate}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td><input type="text" name="refresh" size="3" maxlength="3" value="$U{refresh}"></td></tr></table></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{fontcolour}</b> (<a href="$S?action=colours&amp;session=$U{session}" target="view">$I{viewcolours}</a>)</td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td><input type="text" size="7" maxlength="6" value="$U{colour}" name="colour"></td></tr></table></td></tr></table></td></tr>|,thr();
	if($U{status}>=2 and $C{allowfonts}){
		print qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{fontface}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td><select name="font" size="1"><option value="">* $I{fontdefault} *</option>|;
		foreach(sort keys %F){print '<option style="',get_style($F{$_}),'" ',$U{fontinfo}=~/$F{$_}/?'selected ':'','value="',$_,'">',$_,'</option>'}
		print qq|</select></td><td>&nbsp;</td><td><input type="checkbox" name="bold" id="bold" value="on"|,$U{fontinfo}=~/<i?bi?>/?' checked':'',qq|></td><td><label for="bold"><b>$I{fontbold}</b></label></td><td>&nbsp;</td><td><input type="checkbox" name="italic" id="italic" value="on"|,$U{fontinfo}=~/<b?ib?>/?' checked':'',qq|></td><td><label for="italic"><i>$I{fontitalic}</i></label></td></tr></table></td></tr></table></td></tr>|,thr();
	}
	print qq|<tr><td align="center">$U{displayname}&nbsp;: |,style_this($I{fontexample},$U{fontinfo}),'</td></tr>',thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{boxsizes}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>$I{boxwidth}</td><td><input type="text" name="boxwidth" size="3" maxlength="3" value="$U{boxwidth}"></td>|,$C{allowmultiline}?qq|<td>&nbsp;</td><td>$I{boxheight}</td><td><input type="text" name="boxheight" size="3" maxlength="3" value="$U{boxheight}"></td>|:'',qq|</tr></table></td></tr></table></td></tr>|,thr();
	if($U{status}>=2){
		print qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{entryrefresh}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td><input type="text" name="entryrefresh" size="3" maxlength="3" value="$U{entryrefresh}"></td></tr></table></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{changepass}</b></td></tr><tr><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td align="left">$I{oldpass}</td><td><input type="password" name="oldpass" size="20"></td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{newpass}</td><td><input type="password" name="newpass" size="20"></td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{confirmpass}</td><td><input type="password" name="confirmpass" size="20"></td></tr></table></td></tr></table></td></tr>|,thr();
	}
	print '<tr><td align="center">',submit($I{savechanges}),"</td></tr></table></form><br>$H{backtochat}</center>";
	print_end();
}

sub send_controls{
	print_start('controls');
	print '<center><table cellspacing="7"><tr>';
	print qq|<td><$H{form} target="post">|,hidden('action','post'),hidden('session',$U{session}),submit($I{butreloadp},qq| style="$C{stylerelpost}"|),'</form></td>';
	print qq|<td><$H{form} target="view">|,hidden('action','view'),hidden('session',$U{session}),hidden('nocache','000001'),submit($I{butreloadm},qq| style="$C{stylerelmes}"|),'</form></td>';
	print qq|<td><$H{form} target="view">|,hidden('action','profile'),hidden('session',$U{session}),submit($I{butprofile},qq| style="$C{styleprofile}"|),'</form></td>';
	print qq|<td><$H{form} target="view">|,hidden('action','admin'),hidden('session',$U{session}),submit($I{butadmin},qq| style="$C{styleadmin}"|),'</form></td>' if $U{status}>=6;
	print qq|<td><$H{form} target="view">|,hidden('action','links'),hidden('session',$U{session}),submit($I{butlinks},qq| style="$C{stylerules}"|),'</form></td>' if $C{linksswitch}==1;
	print qq|<td><$H{form} target="view">|,hidden('action','help'),hidden('session',$U{session}),submit($I{butrules},qq| style="$C{stylerules}"|),'</form></td>';
	print qq|<td><$H{form} target="_parent">|,hidden('action','logout'),hidden('session',$U{session}),submit($I{butexit},qq| style="$C{styleexit}"|),'</form></td>';
	print '</tr></table></center>';
	print_end();
}

sub send_entry{
	$C{entrymessage}=~s/<NICK>/$U{displayname}/g;
	$I{entryhelp}=~s/<REFRESH>/$U{entryrefresh}/;
	print_start('view',$U{entryrefresh},"$S?action=view&session=$U{session}&nocache=000000");
	
	print "<center><h1>$C{entrymessage}</h1></center><hr><small>$I{entryhelp}</small>";
	print_end();
}

sub send_logout{
	$C{logoutmessage}=~s/<NICK>/$U{displayname}/g;
	print_start('view');
	print "<center><h1>$C{logoutmessage}</h1>$H{backtologin}</center>";
	print_end();
}

sub send_colours{
	print_start('profile');
	print "<center><h2>$I{colheader}</h2><tt>";
	for(my $red=0x00;$red<=0xFF;$red+=0x33){ 
		for(my $green=0x00;$green<=0xFF;$green+=0x33){ 
			for(my $blue=0x00;$blue<=0xFF;$blue+=0x33){
				my $hcol=sprintf('%02X',$red).sprintf('%02X',$green).sprintf('%02X',$blue);
				print qq|<font color="#$hcol"><b>$hcol</b></font> |;
			}print '<br>';
		}print '<br>';
	}
	print "</tt>$H{backtoprofile}</center>";
	print_end();
}

sub send_login{
	$I{nickhelp}=~s/<MAX>/$C{maxname}/;
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	$C{header}=~s/<IP>/$ENV{REMOTE_ADDR}/g;
	$C{footer}=~s/<IP>/$ENV{REMOTE_ADDR}/g;
	$C{header}=~s/<VER>/$H{versiontag}/g;
	$C{footer}=~s/<VER>/$H{versiontag}/g;
	print_start('login');
	print qq|<center>$C{header}<$H{form} target="_parent">|,hidden('action','login'),qq|<table  $C{tableattributes}><tr title="$I{nickhelp}"><td align="left">$I{nickname}</td><td align="right"><input type="text" name="nick" size="25" style="$C{stylelogintext}"></td></tr><tr title="$I{passhelp}"><td align="left">$I{password}</td><td align="right"><input type="password" name="pass" size="25" style="$C{stylelogintext}"></td></tr>|;
	get_nowchatting();
	unless($T{guestaccess}){
		print qq|<tr><td colspan="2" align="center">$I{selcolguests}<br><select style="$C{stylecolselect};color:#$C{coltxt};background-color:#$C{colbg};" name="colour"><option value="">* |,$C{rndguestcol}?$I{selcolrandom}:$I{selcoldefault},' *</option>';
		print_colours();
		print '</select></td></tr>';
	}
	elsif($C{noguests}){
		print qq|<tr><td colspan="2" align="center">$C{noguests}</td></tr>|;
	}
	print '<tr><td colspan="2" align="center">',submit($C{loginbutton},qq| style="$C{styleenter}"|),"</td></tr></table></form>$C{nowchatting}<br>$C{footer}</center>";
	print_end();
}

sub send_error{my($err,$mes)=@_;
	$err=~s/<NICK>/$U{displayname}/g;
	$mes=htmlsafe($mes).'<br><br>'if$mes;
	print_start('error');
	print "<center><h2>$I{error} $err</h2>$mes$H{backtologin}</center>";
	print_end();
}

sub send_fatal{
	return if $Q{action}[0]=~/^setup|init$/;
	set_config_defaults();
	set_html_vars();
	print_start('error');
	print "<h2>$I{fatalerror}</h2>$_[0]";
	print_end();
}

sub print_chatters{
	print '<table cellspacing="0"><tr>';
	print_waiting()if$T{waitings};
	print qq|<td valign="top"><b>$I{members}</b></td><td>&nbsp;</td><td valign="top">|,join(' &nbsp; ',@M),'</td>',@G?'<td>&nbsp;&nbsp;</td>':''if@M;
	print qq|<td valign="top"><b>$I{guests}</b></td><td>&nbsp;</td><td valign="top">|,join(' &nbsp; ',@G),'</td>'if@G;
	print '</tr></table>';
}

sub print_waiting{
	$I{butcheckwait}=~s/<COUNT>/$T{waitings}/;
	print qq|<td valign="top"><$H{form}>|,hidden('action','admin'),hidden('do','newcomers'),hidden('session',$U{session}),submit($I{butcheckwait},qq| style="$C{stylecheckwait}"|),'</form></td><td>&nbsp;</td>';
}

sub print_memberslist{
	foreach(sort {lc($a) cmp lc($b)} keys %A){
		if(!$_[0] or $A{$_}[1]==$_[0]){
			print qq|<option value="$A{$_}[0]" style="$A{$_}[2]">$_|;
			unless($_[0]){
				print ' ',$I{symdenied}if$A{$_}[1]==0;   
				print ' ',$I{symmod}   if$A{$_}[1]==6;
				print ' ',$I{symadmin} if$A{$_}[1]>=7;
			}
			print '</option>';
		}
	}
}

######################################################################
# content filters
######################################################################

sub print_filters{
	print qq|<tr><td colspan="2" align="left">$I{filterslist}</td></tr>|;
	my $i=1;foreach(split('<>',$C{textfilters})){print_filter($i++,$_)}
	print qq|<tr><td colspan="2" align="left">$I{filtersnew}</td></tr>|;
	print_filter();
}

sub print_filter{my($no,$filter)=@_;
	$no='new' unless $no;
	my($type,$match,$action,$replace,$active)=split('"',$filter);
	$match=htmlactive($match);
	$replace=htmlactive($replace);
	my $fchoose='';
	my @selected;
	my $rxerror;
	if($no eq 'new'){
		$fchoose=' selected';
	}else{
		$fchoose=' disabled';
		# compile regex and check for errors
		if($type==2){
			my $rx='m/$match/';
			eval $rx;
			if($@){
				$rxerror=$I{fregexerror};
				$active=2;
			}
		}
		$selected[$type]=' selected';
		$selected[$action+2]=' selected';
		$selected[$active+5]=' selected';
		$match=htmlsafe($match);
		$replace=htmlsafe($replace);
	}
	print qq|<tr><td colspan=2 align=right><select name="ftype$no"><option value="$type"$fchoose>$I{fchoosetype}</option><option value="$type" disabled>$I{fseparator}</option><option value="1"$selected[1]>$I{ftypetext}</option><option value="2"$selected[2]>$I{ftyperegex}</option></select><input type="text" name="fmatch$no" size="60" value="$match"></td></tr><tr><td colspan=2 align=right><select name="faction$no"><option value="$action"$fchoose>$I{fchooseaction}</option><option value="$action" disabled>$I{fseparator}</option><option value="1"$selected[3]>$I{factionreplace}</option><option value="2"$selected[4]>$I{factionkick}</option><option value="3"$selected[5]>$I{factionpurge}</option></select><input type="text" name="freplace$no" size="60" value="$replace"></td></tr>|;
	print qq|<tr><td colspan=2 align=right>$rxerror &nbsp;<select name="factive$no"><option value="1"$selected[6]>$I{factive}</option><option value="2"$selected[7]>$I{fdisabled}</option><option value="3">$I{fdelete}</option></select></td></tr>| if $active;
	print qq|<tr><td colspan=2>&nbsp;</td></tr>|;
}

sub filters_from_queries{
# type     0: undef   1: text      2: regex
# action   0: undef   1: replace   2: kick     3: purge
# active   0: undef   1: active    2: disabled 3: delete
# 'type"match"action"replacement"active<>....<>....<>'
	my @filter;
	for(my $i=1;;$i++){
		last if !$Q{"ftype$i"}[0];     # empty
		next if $Q{"factive$i"}[0]==3; # delete
		next if $Q{"ftype$i"}[0]!~/^1|2$/;
		next if $Q{"faction$i"}[0]!~/^1|2|3$/;
		next if $Q{"factive$i"}[0]!~/^1|2$/;
		foreach("fmatch$i","freplace$i"){$Q{$_}[0]=~s/^\s+|\s+$//g}
		$Q{"factive$i"}[0]=2 unless $Q{"fmatch$i"}[0];
		push @filter,join('"',$Q{"ftype$i"}[0],htmlsafe($Q{"fmatch$i"}[0]),$Q{"faction$i"}[0],htmlsafe($Q{"freplace$i"}[0]),$Q{"factive$i"}[0]);
	}
	foreach("fmatchnew","freplacenew"){$Q{$_}[0]=~s/^\s+|\s+$//g}
	if($Q{"ftypenew"}[0]=~/^1|2$/ && $Q{"factionnew"}[0]=~/^1|2|3$/ && $Q{"fmatchnew"}[0]ne''){
		push @filter,join('"',$Q{"ftypenew"}[0],htmlsafe($Q{"fmatchnew"}[0]),$Q{"factionnew"}[0],htmlsafe($Q{"freplacenew"}[0]),'1');
	}
	return join('<>',@filter);
}

sub apply_filters{
	my $n;
	foreach(split('<>',$C{textfilters})){
		my($type,$match,$action,$replace,$active)=split('"',$_);
		next unless $match;
		if($active==1){
			$match=htmlactive($match);
			$replace=htmlactive($replace);
			if($type==1){# text
				$match=~s/\s*\|\s*/|/g;
				$match=~s/\|+/|/g;
				$match=~s/^\||\|$//g;
				$match=~s/([^\w\d\s\|])/'\\x'.unpack('H*',$1)/ge;
				my $rx='$n=($U{message}=~s/$match/$replace/ig)';
				eval $rx;
			}
			elsif($type==2){# regex
				# Evaluating arbitrary user-input is a huge security risk!!!
				# => Escape all special characters, only allow $1,$2,.. for replacements.
				$replace=~s/([^\w\d\s\$]|[\$](?![1-9]))/'\\x'.unpack('H*',$1)/ge;
				my $rx='$n=($U{message}=~s/$match/qq{qq{$replace}}/igee)';
				eval $rx;
			}
			if($n>0){# matches found
				$U{autokick}=$action if $action>=2;
				$U{kickmessage}=$replace if $action==3;
			}
		}
		last if $U{autokick}==3;
	}
}

######################################################################
# session management
######################################################################

sub send_command(){
	$U{message} =~ s/^.//; 
	my ($command, $subcommand) = split (/ /, $U{message}, 2);
	if ($command eq 'kick'){
		my ($kickmessage, $user) = split /@/, $subcommand;
		$user =~ s/^\s+|\s+$//g;
		kick_chatter($user,$kickmessage);
		my $nick=$_[0]||$user;
		my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
		while(my $line=shift@lines){
			my %temp=messagehash($line);
			print $MESSAGES $line unless(expiredm($temp{postdate}) or $temp{poster}eq$nick);
		}
		$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
		$U{message}="$U{nickname} kicked and cleared '$user' because '$kickmessage'";
		add_staff_message();
	}
	if ($command eq 'name'){
		$subcommand =~ s/^\s+|\s+$//g;
		kick_chatter($subcommand,"Names need to make sense, not include random letters or numbers, and not be offensive.");
		my $nick=$_[0]||$subcommand;
		my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
		while(my $line=shift@lines){
			my %temp=messagehash($line);
			print $MESSAGES $line unless(expiredm($temp{postdate}) or $temp{poster}eq$nick);
		}
		$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
		open (MYFILE, '>>badnic.txt');
		print MYFILE "$subcommand\n";
		close (MYFILE);
		$U{message}="$U{nickname} kicked and cleared '$subcommand' because of a bad nickname";
		add_staff_message();
	}
	elsif ($command eq 'clean'){
		if ($subcommand == 'room'){
		clean_room()
		}
	}
	elsif ($command eq 'logout'){
		logout_chatter(pack('H*',$subcommand));
		$U{message}.="$U{nickname} logged out '$subcommand'";
		add_staff_message();
	}
	elsif ($command eq 'delmess'){
		$subcommand =~ s/^\s+|\s+$//g;
		my $nick=$_[0]||$subcommand;
		my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
		while(my $line=shift@lines){
			my %temp=messagehash($line);
			print $MESSAGES $line unless(expiredm($temp{postdate}) or $temp{poster}eq$nick);
		}
		$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
		$U{message}="$U{nickname} cleared '$subcommand' messages";
		add_staff_message();
	}
}

sub create_session{
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	$U{nickname}=cleanup_nick($Q{nick}[0]);
	$U{passhash}=hash_this($U{nickname}.$Q{pass}[0]);
	$U{colour}=$Q{colour}[0];
	$U{status}=1;
	send_error($I{errbadnick}) unless valid_nick($U{nickname});
	check_member();# checked before allowed_nick/pass, in case character limits got changed e.g. so that registered nicks are not locked out
	add_user_defaults();
	if($U{status}==1){# no known member, we have a guest:
		send_error($I{errnoguests}) unless $T{guests};
		send_error($I{errbadnick}) unless allowed_nick($U{nickname});
		send_error($I{errbadnick}) if onlynum($U{nickname});
		send_error($I{errbadnick}) if specialchar($U{nickname});
		send_error($I{errbadnick}) if consecutivechar($U{nickname});
		send_error($I{errbadpass}) unless allowed_pass($Q{pass}[0]);
		send_error($I{errbadpass}) if $U{nickname} eq uc $U{nickname};
		#if (grep{/$U{nickname}/} <FILE>){
		open(FILE,"badnic.txt");
    		while (my $line = <FILE>) {
			send_error($I{errbadnick}) if $line =~ /$U{nickname}/
    		}
    		close FILE;
		my $x = substr($U{nickname}, 0, 1);
		my $c = $U{nickname} =~ /$x/g;
		send_error($I{errbadpass}) if length($U{nickname}) eq $c;
		create_waiting_session() if $T{guests}==4;# send guest to waiting room
	}
	write_new_session();
}

sub write_new_session{
	# read and update current sessions
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	my %sids;my $reentry=0;my $inuse=0;my $kicked=0;
	for(my $i=$#lines; $i>=0;$i--){
		my %temp=sessionhash($lines[$i]);
		$sids{$temp{session}}=1;# collect all existing ids
		if($temp{nickname}eq$U{nickname}){# nick already here?
			if($U{passhash}eq$temp{passhash}){
				%U=%temp;
				add_user_defaults();
				$U{status}==0?$kicked=1:$reentry=1;
				splice(@lines,$i,1)if$reentry;
			}else{
				$inuse=1;
			}
		}elsif(similar_nick($temp{nickname},$U{nickname})){
			$inuse=1 if $U{status}==1;
		}
	}
	# create new session:
	unless($inuse or $kicked){
		unless($U{status}==1 and $T{guestaccess}){
			do{$U{session}=hash_this(time.rand().$U{nickname})}while($sids{$U{session}});# check for hash collision
			push(@lines,sessionline(%U));
		}
	}
	print $SESSIONS @lines;
	$ferr=close_file($SESSIONS,'sessions');
	send_error($ferr)if$ferr;
	send_error($I{errbadlogin}) if $inuse;
	send_error($C{kickederror},$U{kickmessage}) if $kicked;
	send_error($I{errnoguests}) if($U{status}==1 and $T{guestaccess});
	clean_room() unless(keys %P);
	add_system_message($C{roomentry}) if $U{status}>3;
}

sub kick_chatter{my($name,$mes)=@_;
	my $kickednick='';
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{nickname}eq$name and $temp{status}!=0){
			if($U{status}>$temp{status} or $U{nickname}eq$name){# verify if status is sufficient to kick
				$temp{status}='0';
				$temp{lastpost}=60*($C{kickpenalty}-$C{guestsexpire})+$^T;
				$temp{kickmessage}=$mes;
				$_=sessionline(%temp);
				$kickednick=style_this($temp{nickname},$temp{fontinfo});
			}
		}
	}
	print $SESSIONS @lines;
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	#add_system_message($C{kickedmessage},$kickednick)if$kickednick;
	return $kickednick;
}

sub logout_chatter{my $name=$_[0];
	my $lonick='';
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	for(my$i=$#lines; $i>=0;$i--){
		my%temp=sessionhash($lines[$i]);
		if($temp{nickname}eq$name and $temp{status}!=0){
			if($U{status}>$temp{status} or $U{nickname}eq$name){# verify if status is sufficient to logout
				splice(@lines,$i,1);
				$lonick=style_this($temp{nickname},$temp{fontinfo});
			}
		}
	}
	print $SESSIONS @lines;
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	return $lonick;
}

sub update_session{
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	if($U{postid}eq$Q{postid}[0]){# ignore double post=reload from browser or proxy
		$Q{message}[0]='';
	}
	elsif($^T-$U{lastpost}<=$C{floodlimit}){# time between posts too short, reject!
		$U{rejected}=$Q{message}[0];
		$Q{message}[0]='';
	}
	else{# valid post
		$U{postid}=substr($Q{postid}[0],0,6);
		$U{lastpost}=$^T;
	}
	foreach(@lines){
		my %temp=sessionhash($_);
		print $SESSIONS $_ unless $temp{session}eq$U{session};
	}
	print $SESSIONS sessionline(%U) if $U{session};
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror},$U{kickmessage}) if $U{status}==0;
	send_error($I{errnoguests}) if($U{status}==1 and $T{guestaccess});
}

sub check_session{
	parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror},$U{kickmessage}) if $U{status}==0;
	send_error($I{errnoguests}) if($U{status}==1 and $T{guestaccess});
}

sub kill_session{
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		print $SESSIONS $_ unless($temp{session}eq$U{session} and $U{status}!=0);
	}
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror},$U{kickmessage}) if($U{status}==0);
	if(scalar keys %P>1){# still chatters in room
		add_system_message($C{roomexit}) if $U{status}>3;  
	}else{clean_room()}
}

sub get_nowchatting{
	parse_sessions(slurp_file('sessions',my$ferr));
	return if$ferr;
	$C{nowchatting}=~s/<NAMES>/join(' &nbsp; ',(@M,@G))/eg;
	$C{nowchatting}=~s/<COUNT>/@M+@G/eg;
	return $C{nowchatting};
}

sub parse_sessions{my @lines=@_;
# returns cleaned up sessions and populates global variables
	my %temp;my $i;%P=();@G=();@M=();$T{admincount}=0;
	# we need admincount first
	for($i=$#lines; $i>=0;$i--){
		%temp=sessionhash($lines[$i]);
		if(expireds($temp{lastpost},$temp{status})){
			splice(@lines,$i,1);
		}
		#elsif($temp{status}>=6){
		#	$T{modcount}++;
		#}
		elsif($temp{status}>=7){
			$T{admincount}++;
		}
	}
	# fill variables, clean up guests if needed
	#$T{hasadmin}=($T{guests}=>3 and !$T{admincount})?1:0;
	#$T{hasmod}=($T{guests}==2 and !$T{modcount})?1:0;
	#$T{allowall}= $T{guests}==1;
	#$T{blockguests}= $T{guests}==0;
	#$T{guestaccess}=($T{hasmod} or $T{hasadmin} or $T{allowall} or !$T{guests});
	$T{guestaccess}=(!$T{guests} or $T{guests}>1 and !$T{admincount})?1:0;
	for($i=$#lines; $i>=0;$i--){
		%temp=sessionhash($lines[$i]);
		if($temp{session}eq$Q{session}[0]){
			%U=%temp;
			add_user_defaults();
		}
		if($temp{status}>=2){
			$P{$temp{nickname}}=[unpack('H*',$temp{nickname}),$temp{status},get_style($temp{fontinfo})];
			$temp{nickname}=~s/\s+/&nbsp;/g;
			push(@M,style_this($temp{nickname},$temp{fontinfo}));
		}elsif($temp{status}==1){
			if($T{guestaccess}){
				splice(@lines,$i,1);
			}else{
				$P{$temp{nickname}}=[unpack('H*',$temp{nickname}),$temp{status},get_style($temp{fontinfo})];
				$temp{nickname}=~s/\s+/&nbsp;/g;
				push(@G,style_this($temp{nickname},$temp{fontinfo}));
			}
		}
	}
	return @lines;
}

sub sessionhash{
	my @f=split('l',$_[0]);  
	my %s=(
		session     =>          $f[ 0] ,
		nickname    =>pack('H*',$f[ 1]),
		status      =>pack('H*',$f[ 2]),
		refresh     =>pack('H*',$f[ 3]),
		fontinfo    =>pack('H*',$f[ 4]),
		lastpost    =>pack('H*',$f[ 5]),
		passhash    =>          $f[ 6] ,
		postid      =>pack('H*',$f[ 7]),
		entryrefresh=>pack('H*',$f[ 8]),
		boxwidth    =>pack('H*',$f[ 9]),
		boxheight   =>pack('H*',$f[10]),
		ip          =>pack('H*',$f[11]),
		useragent   =>pack('H*',$f[12]),
		kickmessage =>pack('H*',$f[13]),
	);
	return %s;
}

sub sessionline{
	my %h=@_;
	my $s= 
		            $h{session}      .'l'.
		unpack('H*',$h{nickname})    .'l'.
		unpack('H*',$h{status})      .'l'.
		unpack('H*',$h{refresh})     .'l'.
		unpack('H*',$h{fontinfo})    .'l'.
		unpack('H*',$h{lastpost})    .'l'.
		            $h{passhash}     .'l'.
		unpack('H*',$h{postid})      .'l'.
		unpack('H*',$h{entryrefresh}).'l'.
		unpack('H*',$h{boxwidth})    .'l'.
		unpack('H*',$h{boxheight})   .'l'.
		unpack('H*',$h{ip})          .'l'.
		unpack('H*',$h{useragent})   .'l'.
		unpack('H*',$h{kickmessage}) .'l'.
		"\n";
	return $s;
}

######################################################################
# waiting room handling
######################################################################

sub create_waiting_session{
	# check if name used in room already
	my @lines=parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if(similar_nick($temp{nickname},$U{nickname})){
			if($temp{passhash}eq$U{passhash}){# reentry, approved already
				%U=%temp;
				add_user_defaults();
				send_error($C{kickederror},$U{kickmessage}) if $U{status}==0;
				send_frameset();
			}
			else{send_error($I{errbadlogin})}# name in use
		}
	}
	# remove expired waiting entries
	@lines=parse_waitings(open_file_rw(my$WAITING,'waiting',$ferr));send_error($ferr)if$ferr;
	my %sids;my $reentry;my $inuse;
	foreach(@lines){
		my %temp=waitinghash($_);
		$sids{$temp{session}}=1;# collect all existing ids
		if(similar_nick($temp{nickname},$U{nickname})){# nick already waiting?
			if($U{passhash}eq$temp{passhash}){
				$reentry=1;
				%U=%temp;
				add_user_defaults();
				$U{status}=1 if $U{status}==2;# needs reapproval since no session in room was made
			}else{
				$inuse=1;
			}
		}
	}
	# create new waiting session:
	unless($inuse or $reentry or $T{guestaccess}){
		$U{status}=1;
		add_user_defaults();
		do{$U{session}=substr(hash_this(time.rand().$U{nickname}),16)}while($sids{$U{session}});# check for hash collision
		push(@lines,waitingline(%U));
	}
	print $WAITING @lines;
	$ferr=close_file($WAITING,'waiting');send_error($ferr)if$ferr;
	send_error($I{errbadlogin}) if $inuse;
	send_error($I{errnoguests}) if $T{guestaccess};
	send_error($I{erraccdenied},$U{kickmessage}) if($U{status}==0);
	send_waiting_room();
}

sub check_waiting_session{
	parse_waitings(slurp_file('waiting',my$err));
	send_error($err)if$err;
	send_error($I{errexpired}) unless $U{session};
	send_error($I{erraccdenied},$U{kickmessage}) if($U{status}==0);
	if($U{status}==2){# approved: create new session, send frameset
		$U{status}=1;
		add_user_defaults();
		write_new_session();
		send_frameset();
	}
}

sub expire_waiting_sessions{
	# cleanup unhandled waitings if guestroom gets opened
	my @lines=parse_waitings(open_file_rw(my$WAITING,'waiting',my$ferr));return if$ferr;
	foreach(@lines){
		my %temp=waitinghash($_);
		print $WAITING $_ if$temp{status}!=1;
	}
	$ferr=close_file($WAITING,'waiting');
}

sub send_waiting_room{
	$I{waitmessage}=~s/<REFRESH>/$C{defaultrefresh}/;
	$I{waitmessage}=~s/<NICK>/$U{displayname}/;
	print_start('wait',$C{defaultrefresh},"$S?action=wait&session=$U{session}&nocache=".substr($^T,-6));
	print "<center><h2>$I{waitroom}</h2>$I{waitmessage}<br><br>";
	print '<hr width="',substr($^T,-2),'%">';
	print "<$H{form}>",hidden('action','wait'),hidden('session',$U{session}),submit($I{butreloadw},qq| style="$C{stylewaitrel}"|),'</form></center>';
	print_end();
}

sub send_waiting_admin{
	my @lines=parse_waitings(slurp_file('waiting',my$ferr));
	send_error($ferr)if$ferr;
	print_start('admin');
	print qq|<center><h2>$I{admwaiting}</h2>|;
	if($T{waitings}){
		print qq|<$H{form}>|,hidden('action','admin'),hidden('do','newcomers'),hidden('session',$U{session}),qq|<table cellpadding="5"><thead align="left"><tr><th><b>$I{nicklist}</b></th><th><b>$I{ip}</b></th><th><b>$I{useragent}</b></th></tr></thead><tbody align="left" valign="middle">|;
		foreach(@lines){
			my %temp=waitinghash($_);
			next if $temp{status}!=1;
			print qq|<tr>|,hidden('alls',$temp{session}),qq|<td><input type="checkbox" name="csid" id="$temp{session}" value="$temp{session}"><label for="$temp{session}">&nbsp;<font color="#$temp{colour}">$temp{nickname}</font></label></td><td>$temp{ip}</td><td>$temp{useragent}</td></tr>|;
		}
		print qq|</tbody></table><br><table><tr><td><input type="radio" name="what" value="allowchecked" id="allowchecked" checked></td><td><label for="allowchecked"> $I{allowchecked}&nbsp;&nbsp;</label></td><td><input type="radio" name="what" value="allowall" id="allowall"></td><td><label for="allowall"> $I{allowall}&nbsp;&nbsp;</label></td><td><input type="radio" name="what" value="denychecked" id="denychecked"></td><td><label for="denychecked"> $I{denychecked}&nbsp;&nbsp;</label></td><td><input type="radio" name="what" value="denyall" id="denyall"></td><td><label for="denyall"> $I{denyall}&nbsp;&nbsp;</label></td></tr><tr><td colspan="8" align="center">$I{denymessage}&nbsp;<input type="text" name="kickmessage" size="45"></td></tr><tr><td colspan="8" align="center">|,submit($I{butallowdeny}),qq|</td></tr></table></form><br>|;
	}else{
		print "$I{waitempty}<br><br>";
	}
	print "$H{backtochat}</center>";
	print_end();
}

sub get_waiting_count{
	# return number of sessions to be approved, for admin-button
	parse_waitings(slurp_file('waiting',my$ferr));
	send_error($ferr)if$ferr;
	return $T{waitings};
}

sub parse_waitings{my @lines=@_;
	# returns cleaned up sessions and populates global variables
	$T{waitings}=0;
	for(my $i=$#lines; $i>=0;$i--){
		my %temp=waitinghash($lines[$i]);
		if(expiredw($temp{timestamp})){
			splice(@lines,$i,1);
		}else{
			if($Q{session}[0]eq$temp{session}){
				%U=%temp;
				add_user_defaults();
			}
			$T{waitings}++ if $temp{status}==1;
		}
	}
	return @lines;
}

sub edit_waiting_sessions{
	my %sids=();my $newstatus=1;
	if($_[0]eq'allowchecked'){
		foreach(@{$Q{csid}}){$sids{$_}=1}
		$newstatus=2;
	}elsif($_[0]eq'denychecked'){
		foreach(@{$Q{csid}}){$sids{$_}=1}
		$newstatus=0;
	}elsif($_[0]eq'allowall'){
		foreach(@{$Q{alls}}){$sids{$_}=1}
		$newstatus=2;
	}elsif($_[0]eq'denyall'){
		foreach(@{$Q{alls}}){$sids{$_}=1}
		$newstatus=0;
	}else{return}
	my @lines=parse_waitings(open_file_rw(my$WAITING,'waiting',my$ferr));send_error($ferr)if$ferr;
	foreach my $wait (@lines){
		my %temp=waitinghash($wait);
		if($temp{status}==1 and $sids{$temp{session}}){
			$temp{status}=$newstatus;
			$temp{kickmessage}=$Q{kickmessage}[0] if $newstatus==0;
		}
		$wait=waitingline(%temp);
	}
	print $WAITING @lines;
	$ferr=close_file($WAITING,'waiting');send_error($ferr)if$ferr;
}

sub waitinghash{
	my @f=split('l',$_[0]);  
	my %w=(
		session    =>          $f[0] ,
		timestamp  =>pack('H*',$f[1]),
		nickname   =>pack('H*',$f[2]),
		passhash   =>          $f[3] ,
		colour     =>pack('H*',$f[4]),
		ip         =>pack('H*',$f[5]),
		useragent  =>pack('H*',$f[6]),
		status     =>pack('H*',$f[7]),
		kickmessage=>pack('H*',$f[8]),
	);
	return %w;
}

sub waitingline{
	my %h=@_;
	my $w= 
		            $h{session}     .'l'.
		unpack('H*',$h{timestamp})  .'l'.
		unpack('H*',$h{nickname})   .'l'.
		            $h{passhash}    .'l'.
		unpack('H*',$h{colour})     .'l'.
		unpack('H*',$h{ip})         .'l'.
		unpack('H*',$h{useragent})  .'l'.
		unpack('H*',$h{status})     .'l'.
		unpack('H*',$h{kickmessage}).'l'.
		"\n";
	return $w;
}

######################################################################
# member handling
######################################################################

sub valid_admin{
	($U{nickname},$U{pass},$U{hexpass})=@_;
	$U{pass}||=pack('H*',$U{hexpass});# masked pass on setup pages
	# superuser?
	$U{passhash}=hash_this($U{nickname}.hash_this($U{nickname}).hash_this($U{pass}).$U{pass});
	my($sudata)=slurp_file('admin',my$ferr);
	send_error($ferr)if$ferr;
	if($U{passhash}eq$sudata){
		$U{status}=9;
		return 2
	}
	# main admin?
	$U{passhash}=hash_this($U{nickname}.$U{pass});
	my @lines=slurp_file('members',$ferr);
	send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$U{nickname} and $temp{passhash}eq$U{passhash} and $temp{status}==8){
			return 1
		}
	}
	# no admin
	return 0
}

sub check_member{  
	my @lines=slurp_file('members',my$ferr);
	send_error($ferr)if$ferr;
	my $similar=0;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$U{nickname}){
			if($temp{passhash}eq$U{passhash}){
				%U=%temp;
				last;
			}else{send_error($I{errbadlogin})}
		}
		$similar=1 if similar_nick($temp{nickname},$U{nickname});
	}
	send_error($I{errbadlogin}) if($U{status}==1 and $similar);
	send_error($I{erraccdenied}) if($U{status}==0 or $U{status}>8);
}

sub read_members{
	my @lines=slurp_file('members',my$ferr);
	send_error($ferr)if$ferr;
	%A=(); 
	foreach(@lines){
		my %temp=memberhash($_);
		$A{$temp{nickname}}=[unpack('H*',$temp{nickname}),$temp{status},get_style("#$temp{colour} $F{$temp{fontface}} <$temp{fonttags}>")];
	}
}

sub register_guest{
	send_admin() if $Q{name}[0]eq'';
	unless($P{pack('H*',$Q{name}[0])}[1]==1){
		$I{errcantreg}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
		send_admin($I{errcantreg});
	}
	my @lines=open_file_rw(my$SESSIONS,'sessions',my$ferr);send_error($ferr)if$ferr;
	my %reg;
	foreach(@lines){
		my %temp=sessionhash($_); 
		if(unpack('H*',$temp{nickname})eq$Q{name}[0] and $temp{status}==1){
			$temp{status}=2;
			%reg=%temp;
			($reg{colour})=$reg{fontinfo}=~/#([a-f0-9]{6})/i;
			print $SESSIONS sessionline(%temp);
		}
		else{
			print $SESSIONS $_ unless expireds($temp{lastpost},$temp{status});
		}
	}
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	unless($reg{status}){
		$I{errcantreg}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
		send_admin($I{errcantreg});
	}
	@lines=open_file_rw(my$MEMBERS,'members',$ferr);send_error($ferr)if$ferr;
	print $MEMBERS @lines;
	foreach(@lines){
		my %temp=memberhash($_);
		if(unpack('H*',$temp{nickname})eq$Q{name}[0]){
			$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
			$I{erralreadyreg}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
			send_admin($I{erralreadyreg});
		}
	}
	print $MEMBERS memberline(%reg);
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	add_system_message($C{regmessage},style_this($reg{nickname},$reg{fontinfo}));
}

sub register_new{
	$Q{name}[0]=cleanup_nick($Q{name}[0]);
	send_admin() if $Q{name}[0]eq'';
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	if($P{$Q{name}[0]}){
		$I{errcantregnew}=~s/<NICK>/$Q{name}[0]/;
		send_admin($I{errcantregnew});
	}
	send_admin($I{errbadnick}) unless valid_nick($Q{name}[0]);
	send_admin($I{errbadpass}) unless allowed_pass($Q{pass}[0]);
	my @lines=open_file_rw(my$MEMBERS,'members',my$ferr);send_error($ferr)if$ferr;
	print $MEMBERS @lines;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$Q{name}[0]){
			$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
			$I{erralreadyreg}=~s/<NICK>/$Q{name}[0]/;
			send_admin($I{erralreadyreg});
		}
	}
	my %reg=(
		nickname    =>$Q{name}[0],
		passhash    =>hash_this($Q{name}[0].$Q{pass}[0]), 
		status      =>'2',
		refresh     =>$C{defaultrefresh},
		colour      =>$C{coltxt},
		fontface    =>'',
		fonttags    =>'',
		entryrefresh=>$C{defaultrefresh}
	);
	print $MEMBERS memberline(%reg);
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	$I{succreg}=~s/<NICK>/$Q{name}[0]/;
	send_admin($I{succreg});
}

sub change_status{
	send_admin()if($Q{name}[0]eq'' or $Q{set}[0]eq'');
	my $nick=pack('H*',$Q{name}[0]);
	if($U{status}<=$Q{set}[0] or $Q{set}[0]!~/^[0267\-]$/){
		$I{errcantstatus}=~s/<NICK>/$nick/;
		send_admin($I{errcantstatus})
	}
	my $found=0;
	my @lines=open_file_rw(my$MEMBERS,'members',my$ferr);send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$nick and $U{status}>$temp{status}){
			$found=1;
			next if $Q{set}[0]eq'-';
			$found=2;
			$temp{status}=$Q{set}[0];
			print $MEMBERS memberline(%temp);
		}
		else{
			print $MEMBERS $_;
		}
	}
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	if($found==1){
		$I{succdelmem}=~s/<NICK>/$nick/;
		send_admin($I{succdelmem})  
	}
	elsif($found==2){
		$I{succstatus}=~s/<NICK>/$nick/;
		send_admin($I{succstatus})  
	}else{
		$I{errcantstatus}=~s/<NICK>/$nick/;
		send_admin($I{errcantstatus})
	}
}

sub amend_profile{
	foreach(qw(refresh boxwidth boxheight entryrefresh)){$Q{$_}[0]=~y/0-9//cd;$Q{$_}[0]=~s/^0+//}
	$U{refresh}=$Q{refresh}[0]||$C{defaultrefresh};
	$U{refresh}=$C{minrefresh}if$U{refresh}<$C{minrefresh};
	$U{refresh}=$C{maxrefresh}if$U{refresh}>$C{maxrefresh};
	$U{colour}=($Q{colour}[0]=~/^[a-f0-9]{6}$/i)?$Q{colour}[0]:$C{coltxt};
	$U{fonttags}='';
	$U{fonttags}.='b'if($Q{bold}[0]and$U{status}>=2);
	$U{fonttags}.='i'if($Q{italic}[0]and$U{status}>=2);
	$U{fontface}=$Q{font}[0]if($F{$Q{font}[0]}and$U{status}>=2);
	$U{fontinfo}="#$U{colour} $F{$U{fontface}} <$U{fonttags}>";
	$U{displayname}=$U{nickname};
	$U{displayname}=~s/\s+/&nbsp;/g;
	$U{displayname}=style_this($U{nickname},$U{fontinfo});
	$U{boxwidth}=$Q{boxwidth}[0]if$Q{boxwidth}[0]>0;
	$U{boxheight}=$Q{boxheight}[0]if$Q{boxheight}[0]>0;
	$U{boxwidth}=$C{boxwidthdef}if$U{boxwidth}>=1000;
	$U{boxheight}=$C{boxheightdef}if$U{boxheight}>=1000;
	$U{entryrefresh}=$Q{entryrefresh}[0]||$C{defaultrefresh};
	$U{entryrefresh}=1if$U{entryrefresh}<1;
	$U{entryrefresh}=$C{defaultrefresh}if$U{entryrefresh}>$C{defaultrefresh};
}

sub save_profile{
	if(!$Q{oldpass}[0]and($Q{newpass}[0]or$Q{confirmpass}[0])){
		check_session();
		send_profile($I{errwrongpass});
	}
	if($Q{newpass}[0]ne$Q{confirmpass}[0]){
		check_session();
		send_profile($I{errdiffpass});
	}
	if($Q{oldpass}[0]and!allowed_pass($Q{newpass}[0])){
		$I{errbadpass}=~s/<MIN>/$C{minpass}/;
		check_session();
		send_profile($I{errbadpass});
	}
	# check and rewrite session
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	$U{oldhash}=$Q{oldpass}[0]?hash_this($U{nickname}.$Q{oldpass}[0]):$U{passhash};
	$U{newhash}=$Q{newpass}[0]?hash_this($U{nickname}.$Q{newpass}[0]):$U{passhash};
	$U{orihash}=$U{passhash};
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{session}eq$U{session} and $temp{status}>0 and $temp{passhash}eq$U{oldhash}){
			amend_profile();
			$U{passhash}=$U{newhash};
			print $SESSIONS sessionline(%U);
		}else{
			print $SESSIONS $_;
		}
	}
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror},'',$U{kickmessage}) if $U{status}==0;
	send_error($I{errnoguests}) if($U{status}==1 and $T{guestaccess});
	send_profile($I{errwrongpass}) if $U{orihash}ne$U{oldhash};
	# rewrite member file
	if($U{status}>=2){
		my $err='';
		my @lines=open_file_rw(my$MEMBERS,'members',$ferr);send_error($ferr)if$ferr;
		foreach(@lines){
			my %temp=memberhash($_);
			if($temp{nickname}eq$U{nickname}){
				$U{sessionstatus}=$U{status};
				$U{status}=$temp{status};
				$err=$I{errwrongpass} unless $temp{passhash} eq $U{orihash};
				print $MEMBERS $err?$_:memberline(%U);
				$U{status}=$U{sessionstatus};
			}
			else{
				print $MEMBERS $_;
			}
		}
		$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
		send_profile($err) if $err;
	}
	send_profile($I{succchanged});
}

sub memberhash{
	my @f=split('l',$_[0]);
	my %m=(
		nickname     =>pack('H*',$f[0]),
		passhash     =>          $f[1] ,
		status       =>pack('H*',$f[2]),
		refresh      =>pack('H*',$f[3]),
		colour       =>pack('H*',$f[4]),
		fontface     =>pack('H*',$f[5]),
		fonttags     =>pack('H*',$f[6]),
		entryrefresh =>pack('H*',$f[7]),
		boxwidth     =>pack('H*',$f[8]),
		boxheight    =>pack('H*',$f[9]),
	);
	return %m;
}

sub memberline{
	my %h=@_;
	my $m=
		unpack('H*',$h{nickname})    .'l'.
		            $h{passhash}     .'l'.
		unpack('H*',$h{status})      .'l'.
		unpack('H*',$h{refresh})     .'l'.
		unpack('H*',$h{colour})      .'l'.
		unpack('H*',$h{fontface})    .'l'.
		unpack('H*',$h{fonttags})    .'l'.
		unpack('H*',$h{entryrefresh}).'l'.
		unpack('H*',$h{boxwidth})    .'l'.
		unpack('H*',$h{boxheight})   .'l'.
		"\n";
	return $m;
}

sub add_user_defaults{
	$U{ip}=$ENV{REMOTE_ADDR};
	$U{useragent}=htmlsafe($ENV{HTTP_USER_AGENT});
	$U{refresh}||=$C{defaultrefresh};
	unless($U{fontinfo}){
		unless($U{colour}=~/^[a-f0-9]{6}$/i){
			$U{colour}=$C{coltxt};
			if($C{rndguestcol}){
				do{$U{colour}=sprintf('%02X',int(rand(256))).sprintf('%02X',int(rand(256))).sprintf('%02X',int(rand(256)))}until(abs(greyval($U{colour})-greyval($C{colbg}))>75);
			}
		}
		$U{fontinfo}="#$U{colour}";
		$U{fontinfo}.=" $F{$U{fontface}} <$U{fonttags}>" if $C{allowfonts};
	}
	($U{colour})=$U{fontinfo}=~/#([0-9A-Fa-f]{6})/;
	$U{style}=get_style($U{fontinfo});
	$U{entryrefresh}||=$C{defaultrefresh};
	$U{boxwidth}||=$C{boxwidthdef};
	$U{boxheight}||=$C{boxheightdef};
	$U{timestamp}||=$^T;
	$U{lastpost}||=$^T;
	$U{postid}||='OOOOOO';
	$U{displayname}=$U{nickname};
	$U{displayname}=~s/\s+/&nbsp;/g;
	$U{displayname}=style_this($U{displayname},$U{fontinfo});
}

######################################################################
# message handling
######################################################################

sub validate_input{
	$U{message}=substr($Q{message}[0],0,$C{maxmessage});
	$U{rejected}=substr($Q{message}[0],$C{maxmessage}) unless $U{rejected};
	if($U{message}=~/&[^;]{0,8}$/ and $U{rejected}=~/^([^;]{0,8};)/){
		$U{message}.=$1;
		$U{rejected}=~s/^$1//;
	}
	if($U{rejected}){
		$U{rejected}=htmlsafe($U{rejected});
		$U{rejected}=~s/<br>(<br>)+/<br><br>/g;
		$U{rejected}=~s/<br><br>$/<br>/;
		$C{allowmultiline}?$U{rejected}=~s/<br>/\n/g:$U{rejected}=~s/<br>/ /g;
		$U{rejected}=~s/^\s+|\s+$//g;
	} 
	$U{message}=htmlsafe($U{message});
	apply_filters();
	if($C{allowmultiline} and $Q{multi}[0]){
		$U{message}=~s/<br>(<br>)+/<br><br>/g;
		$U{message}=~s/<br><br>$/<br>/;
		$U{message}=~s/  / &nbsp;/g;
		$U{message}=~s/<br> /<br>&nbsp;/g;
	}else{
		$U{message}=~s/<br>/ /g;
		$U{message}=~s/^\s+|\s+$//g;
		$U{message}=~s/\s+/ /g;
	}
	create_hotlinks();
	$U{delstatus}=$U{status};
	if($Q{sendto}[0]eq'*'){
		$U{poststatus}='1';
		$U{displaysend}=$C{mesall};
	}
	elsif($Q{sendto}[0]eq'?' and $U{status}>=2){
		$U{poststatus}='2';
		$U{displaysend}=$C{mesmem};
	}
	elsif($Q{sendto}[0]eq'#' and $U{status}>=6){
		$U{poststatus}='6';
		$U{displaysend}=$C{messtaff};
	}
	elsif($C{allowpms}){# known nick in room?
		foreach(keys %P){if($Q{sendto}[0]eq$P{$_}[0]){
			$U{recipient}=$_; 
			$U{displayrecp}=style_this($_,$P{$_}[2]);
		}}
		if($U{recipient}){
			$U{poststatus}='9';
			$U{delstatus}='9';
			$U{displaysend}=$C{mespm};
		}
		else{# nick left already
			$U{message}='';
			$U{rejected}='';
		}
	}
	else{# invalid recipient
		$U{message}='';
		$U{rejected}='';
	}
	$U{displaysend}=~s/<NICK>/$U{displayname}/;
	$U{displaysend}=~s/<RECP>/$U{displayrecp}/;
}

sub formsafe{my $m=$_[0];
	$m=~s/&/&amp;/g;
	$m=~s/"/&quot;/g;
	$m=~s/</&lt;/g;
	$m=~s/>/&gt;/g;
	return $m;
}

sub htmlsafe{my $m=$_[0];
	$m=~s/&(?![\w\d\#]{2,8};)/&amp;/g;
	$m=~s/</&lt;/g;
	$m=~s/>/&gt;/g;
	$m=~s/"/&quot;/g;
	$m=~s/\r\n/<br>/g;
	$m=~s/\n/<br>/g;
	$m=~s/\r/<br>/g;
	return $m;
}

sub htmlactive{my $m=$_[0];
	$m=~s/&quot;/"/g;
	$m=~s/&lt;/</g;
	$m=~s/&gt;/>/g;
	$m=~s/&amp;/&/g;
	$m=~s/\r\n/\n/g;
	$m=~s/\r/\n/g;
	return $m;
}

sub create_hotlinks{
	return unless $C{createlinks};
	#######################################################################################
	# Make hotlinks for URLs, redirect through dereferrer script to prevent session leakage
	#######################################################################################
	# 1. all explicit schemes with whatever xxx://yyyyyyy
	$U{message}=~s~(\w*://[^\s<>]+)~<<$1>>~ig;
	# 2. valid URLs without scheme:
	$U{message}=~s~((?:[^\s<>]*:[^\s<>]*@)?[a-z0-9\-]+(?:\.[a-z0-9\-]+)+(?::\d*)?/[^\s<>]*)(?![^<>]*>)~<<$1>>~ig; # server/path given
	$U{message}=~s~((?:[^\s<>]*:[^\s<>]*@)?[a-z0-9\-]+(?:\.[a-z0-9\-]+)+:\d+)(?![^<>]*>)~<<$1>>~ig; # server:port given
	$U{message}=~s~([^\s<>]*:[^\s<>]*@[a-z0-9\-]+(?:\.[a-z0-9\-]+)+(?::\d+)?)(?![^<>]*>)~<<$1>>~ig; # au:th@server given
	# 3. likely servers without any hints but not filenames like *.rar zip exe etc.
	$U{message}=~s~((?:[a-z0-9\-]+\.)*[a-z0-9]{16}\.onion)(?![^<>]*>)~<<$1>>~ig;# *.onion
	$U{message}=~s~([a-z0-9\-]+(?:\.[a-z0-9\-]+)+(?:\.(?!rar|zip|exe|gz|7z|bat|doc)[a-z]{2,}))(?=[^a-z0-9\-\.]|$)(?![^<>]*>)~<<$1>>~ig;# xxx.yyy.zzz
	# Convert every <<....>> into proper links:
	$U{message}=~s/<<([^<>]+)>>/url2hotlink($1)/ge;
}

sub url2hotlink{
	# check for surrounding  < > " " ( ) etc. and create hotlink
	my($pre,$url,$app)=$_[0]=~/^((?:&\w{1,7};)*)(.*?)((?:&\w{1,7};|[\{\[\(\)\]\}])*)$/;
	my $href= $url;
	my $path = substr $url, rindex($url, '/') + 1;
	$path = substr $path, rindex($path, '_') + 1;
	$url =~ s/www\.(.*\.(?:net|org|com|onion|ru|biz)).*/$1/;
	$url =~ s/https?\:\/\/(.*\.(?:net|org|com|onion|ru|biz)).*/$1/;
	$url =~ s!^https?://(?:www\.)?!!i;
	$url = "$url:$path" unless $url eq $path|$url or $path eq "";
	$href=~s/([\:\/\?\#\[\]\@\!\$\&\'\(\)\*\+\,\;\=\%])/sprintf("%%%02X",ord($1))/eg;
	return qq|$pre<a href="|.($C{useextderef}?$C{extderefurl}:$S).qq|?action=redirect&amp;url=$href" target="_blank">$url</a>$app|;
}

sub add_message{
	return unless $U{message};
	my %newmessage=(
		postdate  =>$^T,
		postid    =>$U{postid},
		poststatus=>$U{poststatus},
		poster    =>$U{nickname},
		recipient =>$U{recipient},
		text      =>$U{displaysend}.style_this($U{message},$U{fontinfo}),
		delstatus =>$U{delstatus}
	);
	write_message(%newmessage);
}

sub add_staff_message{
	my $mes=$_[0]||$U{message};return unless $mes;
	my $nick=$_[1]||$U{displayname};
	$mes=~s/<NICK>/$nick/g;
	$C{messtaff}=~s/<NICK>//g;
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>'6',
		text=>$C{messtaff}.$mes,
		delstatus=>'9'
	);
	write_message(%sysmessage);
}

sub add_system_message{
	my $mes=$_[0]||$U{message};return unless $mes;
	my $nick=$_[1]||$U{displayname};
	$mes=~s/<NICK>/$nick/g;
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>'1',
		text=>$mes,
		delstatus=>'9'
	);
	write_message(%sysmessage);
}

sub write_message{my%message=@_;
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line unless expiredm($temp{postdate});
	}
	print $MESSAGES messageline(%message);
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub clean_room{
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>'1',
		text=>$C{roomclean},
		delstatus=>'9'
	);
	my $ferr=write_file('messages',messageline(%sysmessage));send_error($ferr)if$ferr;
}

sub clean_selected{
	my %mids;foreach(@{$Q{mid}}){$mids{$_}=1}
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my $line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line unless(expiredm($temp{postdate}) or $mids{$temp{postdate}.$temp{postid}});
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub del_last_message{
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	for(my$i=@lines;$i>=0;$i--){
		my %temp=messagehash($lines[$i]);
		if($U{nickname}eq$temp{poster}){
			splice(@lines,$i,1);
			last;
		}
	}
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line unless expiredm($temp{postdate});
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub del_all_messages{
	my $nick=$_[0]||$U{nickname};
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my $line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line unless(expiredm($temp{postdate}) or $temp{poster}eq$nick);
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub print_messages{my $delstatus=$_[0];
	my @lines=slurp_file('messages',my$ferr);
	return if$ferr;
	while(my $line=pop@lines){
		my %message=messagehash($line);
		if($delstatus){# select messages to delete
			if($U{status}>$message{delstatus}){ 
				print qq|<input type="checkbox" name="mid" id="$message{postdate}$message{postid}" value="$message{postdate}$message{postid}"><label for="$message{postdate}$message{postid}">&nbsp;$message{text}</label><br>|unless expiredm($message{postdate});
			}
		}
		elsif($U{status}>=$message{poststatus} or $U{nickname}eq$message{poster} or $U{nickname}eq$message{recipient}){ 
			print "$message{text}<br>" unless expiredm($message{postdate});  
		}
	}
}

sub messagehash{
	my @fields=split('l',$_[0]);  
	my %mes=(
		postdate  =>pack('H*',$fields[0]),
		postid    =>pack('H*',$fields[1]),
		poststatus=>pack('H*',$fields[2]),
		poster    =>pack('H*',$fields[3]),
		recipient =>pack('H*',$fields[4]),
		text      =>pack('H*',$fields[5]),
		delstatus =>pack('H*',$fields[6])
	);
	return %mes;
}

sub messageline{
	my %mes=@_;
	my $m=
		unpack('H*',$mes{postdate}).'l'.
		unpack('H*',$mes{postid}).'l'.
		unpack('H*',$mes{poststatus}).'l'.
		unpack('H*',$mes{poster}).'l'.
		unpack('H*',$mes{recipient}).'l'.
		unpack('H*',$mes{text}).'l'.
		unpack('H*',$mes{delstatus})."l\n";
	return $m;
}

######################################################################
# Superuser Setup
######################################################################

sub send_init{
	my $result=create_files();
	$I{setsuhelp}=~s/<DATA>/$datadir/;
	$I{nickhelp}=~s/<MAX>/$C{maxname}/;
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	print_start('admin');
	print "<center><h2>LE&nbsp;CHAT - $I{initsetup}</h2>";
	print "<$H{form}>",hidden('action','init'),qq|<table cellspacing="0" width="1"><tr><td align=center><h3>$I{setsu}</h3><table cellspacing="0"><tr title="$I{nickhelp}"><td>$I{setsunick}</td><td><input type="text" name="sunick" size="15"></td></tr><tr title="$I{passhelp}"><td>$I{setsupass}</td><td><input type="text" name="supass" size="15"></td></tr><tr title="$I{passhelp}"><td>$I{setsupassconf}</td><td><input type="text" name="supassc" size="15"></td></tr></table><br><br></td></tr><tr><td align="left">$I{setsuhelp}<br><br><br></td></tr><tr><td align="center">|;
	print qq|<h3>$I{initback}</h3></td></tr><tr><td align="left">$I{initbackhelp}<br></td></tr><tr><td align="center"><textarea name="backupdata" rows="8" cols="80" wrap="off">$result</textarea><br><br></td></tr><tr><td align="center"><tr><td align="center"><br>|,submit($I{initbut}),"</td></tr></table></form><br>$H{versiontag}</center>";
	print_end();
}

sub create_files{
	my $result='';
	# create directories if needed
	my @dirs=split('/',$datadir);my $dir='';
	while($_=shift@dirs){$dir.=$_;mkdir($dir,0700) unless -d$dir;$dir.='/'}
	chmod(0700,$datadir);
	# create files, keep existing ones
	create_file(qw(config members sessions messages waiting langedit));
	# check initial data in lechat.txt
	if(-e'./lechat.txt'){
		my $backupdata='';
		sysopen(LECHAT,'./lechat.txt',O_RDONLY) or return "$I{initlechattxt}\n$I{errfile} (lechat.txt/open)";
		flock(LECHAT,LOCK_SH) or return "$I{initlechattxt}\n$I{errfile} (lechat.txt/lock)";
		while(<LECHAT>){$backupdata.=$_};
		close(LECHAT);
		$result=get_restore_results('',$backupdata);
		$result="$I{initlechattxt}\n$result";
		unlink('./lechat.txt');
		load_config();
	}
	return $result;
}

sub init_chat{
	$I{suerrbadnick}=~s/<MAX>/$C{maxname}/;
	$I{suerrbadpass}=~s/<MIN>/$C{minpass}/;
	# restore backups if given
	my $restore=$I{invalidbackup};
	$restore=get_restore_results() if $Q{backupdata}[0];
	$restore=~s/\n/<br>/g;
	# write superuser into "admin"
	my $suwrite;
	if(-e"$datadir/admin"){
		$suwrite=$I{suerrfileexist};
	}elsif(!valid_nick($Q{sunick}[0])){
		$suwrite=$I{suerrbadnick};
	}elsif(!allowed_pass($Q{supass}[0])){
		$suwrite=$I{suerrbadpass};
	}elsif($Q{supass}[0]ne$Q{supassc}[0]){
		$suwrite=$I{suerrbadpassc};
	}else{# all good data here
		$suwrite=write_admin(hash_this($Q{sunick}[0].hash_this($Q{sunick}[0]).hash_this($Q{supass}[0]).$Q{supass}[0]));
	}
	# Print results:
	print_start('admin');
	print "<center><h2>LE&nbsp;CHAT - $I{initsetup}</h2><br><h3>$I{setsu}</h3>$suwrite<br><br><br><h3>$I{initback}</h3>$restore<br><br><br>";
	print "<$H{form}>",hidden('action','setup'),hidden('nick',$Q{sunick}[0]),hidden('hexpass',unpack('H*',$Q{supass}[0])),submit($I{initgotosetup}),"</form><br>$H{versiontag}</center>";
	print_end();
}

sub write_admin{
	write_file('admin',$_[0]);
	# read and verify data
	my($suverify)=slurp_file('admin');
	return $I{suwritesucc}if($_[0]eq$suverify);
	# delete again if not written correctly
	delete_file('admin');
	return $I{suwritefail};
}

sub change_admin_status{
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	my $err;my %temp;
	return $I{errnonick} unless $Q{admnick}[0];
	return $I{errbaddata} unless $Q{what}[0]=~/^new|up|down$/;
	if($Q{what}[0]eq'new'){
		return $I{errbadnick} unless valid_nick($Q{admnick}[0]);
		return $I{errbadpass} unless allowed_pass($Q{admpass}[0]);
		$Q{admnick}[0]=unpack('H*',cleanup_nick($Q{admnick}[0]));
	}
	my @lines=open_file_rw(my$MEMBERS,'members',my$ferr);send_error($ferr)if$ferr;
	foreach(@lines){
		%temp=memberhash($_);
		if(unpack('H*',$temp{nickname})eq$Q{admnick}[0]){
			if($Q{what}[0]eq'new'){$err=$I{errexistnick}}
			elsif($Q{what}[0]eq'up'){
				if($temp{status}==7){$temp{status}=8;$err=$I{raisemainsucc}}
				elsif($temp{status}==8){$err=$I{raisemaindone}}
				else{$err=$I{raisemainfail}}
			}
			elsif($Q{what}[0]eq'down'){   
				if($temp{status}==8){$temp{status}=7;$err=$I{lowerregsucc}}
				elsif($temp{status}==7){$err=$I{lowerregdone}}
				else{$err=$I{lowerregfail}}
			}
			print $MEMBERS memberline(%temp);
		}
		else{
			print $MEMBERS $_;
		}
		$err=~s/<NICK>/$temp{nickname}/ if $err;
	}
	if($Q{what}[0]eq'new' and !$err){
		%temp=(nickname     =>pack('H*',$Q{admnick}[0]),
		       passhash     =>hash_this(pack('H*',$Q{admnick}[0]).$Q{admpass}[0]),
		       status       =>8,
		       refresh      =>$C{defaultrefresh},
		       colour       =>$C{coltxt},
		       entryrefresh =>$C{defaultrefresh},
		       boxwidth     =>$C{boxwidthdef},
		       boxheight    =>$C{boxheightdef});
		print $MEMBERS memberline(%temp);
		$err=$I{newmainreg};
		$err=~s/<NICK>/$temp{nickname}/;
	}
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	return $err;
}

######################################################################
# backup and restore
######################################################################

sub get_backup{my $fname=$_[0];
	my $finfo='langedit'eq$fname?'LANGUAGE':uc($fname);
	my $blob=join('n',slurp_file($fname,my$err)).'n';
	return $err if $err;
	my $fcomm=get_timestamp((stat("$datadir/$fname"))[9])." - $C{title}";
	$fcomm="Language: $I{languagename} ($I{languagecode}) - $version ($lastchanged)"if'language'eq$fname;
	$fcomm="Language: $L{languagename} ($L{languagecode}) - $version ($lastchanged)"if'langedit'eq$fname;
	$blob=~s/[^a-f0-9ln]//gi;
	$blob.='h'.hash_this($blob).'hi'.$finfo.'i';
	$blob="-----BEGIN LE CHAT $finfo-----\n$fcomm\n\n".encode_this($blob)."-----END LE CHAT $finfo-----";
	return $blob;
}

sub get_restore_results{my($fname,$bdata)=@_;
	$fname||='language config members';
	$bdata||=$Q{backupdata}[0];
	$bdata=~s/\r\n/<br>/g;
	$bdata=~s/\n/<br>/g;
	$bdata=~s/\r/<br>/g;
	$bdata=~s/<br>/\n/g;
	(my $conf)=$bdata=~/-----BEGIN LE CHAT CONFIG-----.*?\n\n(.*)-----END LE CHAT CONFIG-----/s;
	(my $memb)=$bdata=~/-----BEGIN LE CHAT MEMBERS-----.*?\n\n(.*)-----END LE CHAT MEMBERS-----/s;
	(my $lang)=$bdata=~/-----BEGIN LE CHAT LANGUAGE-----.*?\n\n(.*)-----END LE CHAT LANGUAGE-----/s;
	return $I{invalidbackup} unless($memb or $conf or $lang);
	my $result='';
	$result.=restore_file('langedit',$lang)."\n"if$fname=~/langedit/ and$lang;
	$result.=restore_file('language',$lang)."\n"if$fname=~/language/ and$lang;
	$result.=restore_file('config'  ,$conf)."\n"if$fname=~/config/   and$conf;
	$result.=restore_file('members' ,$memb)."\n"if$fname=~/members/  and$memb;
	return $result;
}

sub restore_file{my($fname,$fdata)=@_;
	my $finfo='langedit'eq$fname?'LANGUAGE':uc($fname);
	my $ftype=substr($fname,0,4);
	my $content=decode_this($fdata);
	my($blob,$hash,$info)=$content=~/^([a-f0-9ln]*)h([a-f0-9]+)hi([A-Z]+)i$/;
	if(hash_this($blob)eq$hash and $finfo eq $info){
		$blob=~tr/n/\n/s;
		my $ferror=write_file($fname,$blob);
		if($ferror){return $I{$ftype.'restfail'}.' '.$ferror}
		load_config();
		return $I{$ftype.'restsucc'};
	}
	else{
		return $I{$ftype.'restinval'};
	}
}

sub load_langedit{
	if(-e"$datadir/langedit"){
		my @lines=slurp_file('langedit',my$ferr);
		send_error($ferr)if$ferr;
		foreach(@lines){
			next unless /^[0-9a-f]/;
			my($ikey,$ival)=split('l',$_);
			$L{pack('H*',$ikey)}=pack('H*',$ival);
		}
	}
}

sub save_langedit{
	open_file_wo(my$LANG,'langedit',my$ferr);send_error($ferr)if$ferr;
	my $start=tell(DATA);
	while(<DATA>){
		my($ikey,$ival)=$_=~/^([a-z_]+)\s*=(.+)/i;
		next unless $ikey;
		$ival=$Q{$ikey}[0]unless'stop_action'eq$ikey;
		$ival=~s/^\s*|\s*$//g;$ival=~s/\n//;$ival=~s/\r//;
		$ival=htmlactive($ival);
		print $LANG unpack('H*',$ikey),'l',unpack('H*',$ival),"l\n" if $ival;
	}
	seek(DATA,$start,0);
	$ferr=close_file($LANG,'langedit');send_error($ferr)if$ferr;
}

######################################################################
# file handling
######################################################################

sub get_guests_access{-s"$datadir/guests"||0}
sub get_chat_access{-s"$datadir/access"||0}

sub set_guests_access{
	return if($_[0]<0 or $_[0]>3);
	write_file('guests','#'x$_[0]);
	expire_waiting_sessions()if$_[0]<3;
	$T{guests}=get_guests_access();
}

sub set_chat_access{
	return if($_[0]<0 or $_[0]>2);
	write_file('access','#'x$_[0]);
	$T{access}=get_chat_access();
}

sub slurp_file{# name,error
	sysopen(my$FH,"$datadir/$_[0]",O_RDONLY) or $_[1]="$I{errfile} ($_[0]/open)" and return;
	flock($FH,LOCK_SH) or $_[1]="$I{errfile} ($_[0]/lock)" and return;
	my @lines=<$FH>;
	close($FH) or $_[1]="$I{errfile} ($_[0]/close)" and return;
	return @lines;
}

sub write_file{# name,text
	sysopen(my$FH,"$datadir/$_[0]",O_WRONLY|O_TRUNC|O_CREAT,0600) or return "$I{errfile} ($_[0]/open)";
	flock($FH,LOCK_EX) or return "$I{errfile} ($_[0]/lock)";
	print $FH $_[1] or return "$I{errfile} ($_[0]/print)";
	close($FH) or return "$I{errfile} ($_[0]/close)";
	return '';
}

sub append_file{# name,text
	sysopen(my$FH,"$datadir/$_[0]",O_WRONLY|O_APPEND|O_CREAT,0600) or return "$I{errfile} ($_[0]/open)";
	flock($FH,LOCK_EX) or return "$I{errfile} ($_[0]/lock)";
	print $FH $_[1] or return "$I{errfile} ($_[0]/print)";
	close($FH) or return "$I{errfile} ($_[0]/close)";
	return '';
}

sub open_file_rw{# FH,name,error
	sysopen($_[0],"$datadir/$_[1]",O_RDWR|O_CREAT,0600) or $_[2]="$I{errfile} ($_[1]/open)" and return;
	flock($_[0],LOCK_EX) or $_[2]="$I{errfile} ($_[1]/lock)" and return;
	my $FH=$_[0];
	my @lines=<$FH>;
	seek($_[0],0,0) or $_[2]="$I{errfile} ($_[1]/seek)" and return;
	truncate($_[0],0) or $_[2]="$I{errfile} ($_[1]/truncate)" and return;
	return @lines;
}

sub open_file_wo{# FH,name,error
	sysopen($_[0],"$datadir/$_[1]",O_WRONLY|O_TRUNC|O_CREAT,0600) or $_[2]="$I{errfile} ($_[1]/open)" and return;
	flock($_[0],LOCK_EX) or $_[2]="$I{errfile} ($_[1]/lock)" and return;
}

sub open_file_ro{# FH,name,error
	sysopen($_[0],"$datadir/$_[1]",O_RDONLY) or $_[2]="$I{errfile} ($_[1]/open)" and return;
	flock($_[0],LOCK_SH) or $_[2]="$I{errfile} ($_[1]/lock)" and return;
}

sub close_file{# FH,name
	close($_[0]) or return "$I{errfile} ($_[1]/close)";
	return '';
}

sub create_file{foreach(@_){write_file($_)unless(-e"$datadir/$_")}}
sub delete_file{foreach(@_){unlink("$datadir/$_")}}

######################################################################
# this and that
######################################################################

sub expiredm{($^T-$_[0]>60*$C{messageexpire})}
sub expireds{($^T-$_[0]>60*($_[1]>1?$C{sessionexpire}:$C{guestsexpire}))}
sub expiredw{($^T-$_[0]>60*$C{waitingexpire})}
sub valid_nick{!($_[0]=~/[^\w\d\s\(\)\[\]\{\}\=\/\-\!\@\#\$\%\?\+\*\^\.]/g or $_[0]!~/[a-z0-9]/i)}
sub allowed_nick{$_[0]=~/^.{4,$C{maxname}}$/}
sub specialchar{$_[0] =~ m/[^a-zA-Z0-9]/}
sub onlynum{$_[0] =~ /^(?![A-Za-z]).*/}
sub allowed_pass{($_[0]=~/^.{$C{minpass},}$/)}
sub consecutivechar{$_[0] =~ /(.)\1{2}/}
sub similar_nick{my$x=lc($_[0]);my$y=lc($_[1]);$x=~y/a-z0-9//cd;$y=~y/a-z0-9//cd;$x eq $y?1:0}
sub cleanup_nick{my$nick=$_[0];$nick=~s/^\s+//;$nick=~s/\s+$//;$nick=~s/\s+/ /g;$nick}
sub hash_this{require Digest::MD5;Digest::MD5::md5_hex($_[0])}
sub encode_this{require MIME::Base64;MIME::Base64::encode_base64($_[0])}
sub decode_this{require MIME::Base64;MIME::Base64::decode_base64($_[0])}
sub get_timestamp{my($sec,$min,$hour,$day,$mon,$year)=gmtime($_[0]||$^T);$year+=1900;$mon++;foreach($sec,$min,$hour,$day,$mon){$_=substr('0'.$_,-2,2)}return"$year-$mon-$day $hour:$min:$sec"}

sub get_timeout{ # lastpost, status
	my $s=$_[0]+(60*($_[1]>1?$C{sessionexpire}:$C{guestsexpire}))-$^T;
	my $m=int($s/60);$s-=$m*60;
	my $h=int($m/60);$m-=$h*60;
	$s=substr('0'.$s,-2,2);
	$m=substr('0'.$m,-2,2)if$h;
	return $h?"$h:$m:$s":"$m:$s";
}

sub print_colours{
	# Prints a short list with selected named HTML colours and filters out illegible text colours for the given background.
	# It's a simple comparison of weighted grey values. This is not very accurate but gets the job done well enough.
	# If you want more accuracy, do some research about "Delta E", though the serious math involved there is not worth the effort just for this here I guess. ;)
	my %colours=(Beige=>'F5F5DC',Black=>'000000',Blue=>'0000FF',BlueViolet=>'8A2BE2',Brown=>'A52A2A',Cyan=>'00FFFF',DarkBlue=>'00008B',DarkGreen=>'006400',DarkRed=>'8B0000',DarkViolet=>'9400D3',DeepSkyBlue=>'00BFFF',Gold=>'FFD700',Grey=>'808080',Green=>'008000',HotPink=>'FF69B4',Indigo=>'4B0082',LightBlue=>'ADD8E6',LightGreen=>'90EE90',LimeGreen=>'32CD32',Magenta=>'FF00FF',Olive=>'808000',Orange=>'FFA500',OrangeRed=>'FF4500',Purple=>'800080',Red=>'FF0000',RoyalBlue=>'4169E1',SeaGreen=>'2E8B57',Sienna=>'A0522D',Silver=>'C0C0C0',Tan=>'D2B48C',Teal=>'008080',Violet=>'EE82EE',White=>'FFFFFF',Yellow=>'FFFF00',YellowGreen=>'9ACD32');
	my $greybg=greyval($C{colbg});
	foreach(sort keys %colours){
		print qq|<option value="$colours{$_}" style="color:#$colours{$_}">$I{$_}</option>|unless(abs($greybg-greyval($colours{$_}))<75);
	}
}

sub greyval{hex(substr($_[0],0,2))*.3+hex(substr($_[0],2,2))*.59+hex(substr($_[0],4,2))*.11}

sub get_style{my $styleinfo="@_";
	(my $fbold)=$styleinfo=~/(<i?bi?>|:bold)/;
	(my $fitalic)=$styleinfo=~/(<b?ib?>|:italic)/;
	(my $fsmall)=$styleinfo=~/(size="-1"|:smaller)/;
	(my $fcolour)=$styleinfo=~/(#.{6})/;
	(my $fface)=$styleinfo=~/face="([^"]+)"/;
	(my $sface)=$styleinfo=~/font-family:([^;]+);/;
	if($fface ne ''){$sface=$fface;$sface=~s/^/'/;$sface=~s/$/'/;$sface=~s/,/','/g}
	else{$fface=$sface;$fface=~s/'//}
	my $fstyle='';
	$fstyle.="color:$fcolour;"if$fcolour;
	$fstyle.="font-family:$sface;"if$sface;
	$fstyle.='font-size:smaller;'if$fsmall;
	$fstyle.='font-style:italic;'if$fitalic;
	$fstyle.='font-weight:bold;'if$fbold;
	return $fstyle;
}

sub style_this{my($text,$styleinfo)=@_;
	(my $fbold)=$styleinfo=~/(<i?bi?>|:bold)/;
	(my $fitalic)=$styleinfo=~/(<b?ib?>|:italic)/;
	(my $fsmall)=$styleinfo=~/(size="-1"|:smaller)/;
	(my $fcolour)=$styleinfo=~/(#.{6})/;
	(my $fface)=$styleinfo=~/face="([^"]+)"/;
	(my $sface)=$styleinfo=~/font-family:([^;]+);/;
	if($fface ne ''){$sface=$fface;$sface=~s/^/'/;$sface=~s/$/'/;$sface=~s/,/','/g}
	else{$fface=$sface;$fface=~s/'//}
	my $fstyle='';
	$fstyle.="color:$fcolour;"if$fcolour;
	$fstyle.="font-family:$sface;"if$sface;
	$fstyle.='font-size:smaller;'if$fsmall;
	$fstyle.='font-style:italic;'if$fitalic;
	$fstyle.='font-weight:bold;'if$fbold;
	my $fstart='<font';
	$fstart.=qq| color="$fcolour"|if$fcolour;
	$fstart.=qq| face="$fface"|if$fface;
	$fstart.=qq| size="-1"|if$fsmall;
	$fstart.=qq| style="$fstyle"|if$fstyle;
	$fstart.='>';
	$fstart.='<b>'if$fbold;
	$fstart.='<i>'if$fitalic;
	my $fend='';
	$fend.='</i>'if$fitalic;
	$fend.='</b>'if$fbold;
	$fend.='</font>';
	return "$fstart$text$fend";
}

######################################################################
# configuration, defaults and internals
######################################################################

sub load_config{
	set_internal_defaults();
	if(-e"$datadir/language"){# load language file
		open_file_ro(my$LANG,'language',my$ferr);send_fatal($ferr)if$ferr;
		while(<$LANG>){
			next unless /^[0-9a-f]/;
			my($ikey,$ival)=split('l',$_);
			$ikey=pack('H*',$ikey);
			$ival=pack('H*',$ival);
			last if('stop_action'eq$ikey and $ival=~/-$Q{action}[0]-/);# only load what we need
			$I{$ikey}=$ival;
		}
		$ferr=close_file($LANG,'language');send_fatal($ferr)if$ferr;
	}
	set_config_defaults();
	open_file_ro(my$CONFIG,'config',my$ferr);send_fatal($ferr)if$ferr;
	while(<$CONFIG>){
		next unless /^[0-9a-f]/;
		my($ckey,$cval)=split('l',$_);
		$ckey=pack('H*',$ckey);
		$cval=pack('H*',$cval);
		last if('stop_action'eq$ckey and $cval=~/-$Q{action}[0]-/);# only load what we need
		$C{$ckey}=$cval;
	}
	$ferr=close_file($CONFIG,'config');send_fatal($ferr)if$ferr;
	set_html_vars();
	$T{guests}=get_guests_access();# guest settings
	$T{access}=get_chat_access();# suspended?
}

sub save_config{
	open_file_wo(my$CONFIG,'config',my$ferr);send_error($ferr)if$ferr;
	foreach(qw(redirifsusp redirtourl title favicon kickederror coltxt colbg collnk colvis colact sessionexpire guestsexpire messageexpire waitingexpire kickpenalty defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidth boxheight allowmultiline allowfonts allowpms cssglobal styleback csserror cssview csswait stylecheckwait stylewaitrel roomentry useextderef createlinks linksswitch))
		{print $CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print $CONFIG unpack('H*','stop_action'),'l',unpack('H*','-view-wait-redirect-'),"l\n";
	foreach(qw(mesall mesmem mespm messtaff csspost styleposttext stylepostsend stylesendlist styledellast styledelall styleswitch extderefurl textfilters kickedmessage))
		{print $CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print $CONFIG unpack('H*','stop_action'),'l',unpack('H*','-post-delete-'),"l\n";
	foreach(qw(header footer noguests guestaccess rndguestcol loginbutton nowchatting csslogin stylelogintext stylecolselect styleenter tableattributes frameattributes framesizes))
		{print $CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print $CONFIG unpack('H*','stop_action'),'l',unpack('H*','--'),"l\n";
	foreach(qw(csscontrols stylerelpost stylerelmes styleprofile styleadmin stylerules styleexit cssprofile))
		{print $CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print $CONFIG unpack('H*','stop_action'),'l',unpack('H*','-controls-profile-colours-'),"l\n";
	foreach(qw(cssrules rulestxt links entrymessage roomexit logoutmessage roomclean))
		{print $CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print $CONFIG unpack('H*','stop_action'),'l',unpack('H*','-help-entry-login-logout-'),"l\n";
	foreach(qw(regmessage styledelsome cssadmin lastchangedby lastchangedat))
		{print $CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print $CONFIG unpack('H*','stop_action'),'l',unpack('H*',''),"l\n";
	$ferr=close_file($CONFIG,'config');send_error($ferr)if$ferr;
}

sub set_config{
	foreach(keys %C){$C{$_}=htmlactive($Q{$_}[0]);$C{$_}=~s/^\s+|\s+$//g;}
	$C{textfilters}=filters_from_queries();
	$C{lastchangedby}=$U{nickname};
	$C{lastchangedat}=get_timestamp();
	check_config();
	set_html_vars();
}

sub check_config{
	# Revert to defaults if invalid or empty
	foreach(qw(colbg coltxt collnk colvis colact)){$C{$_}=''if$C{$_}!~/^[a-f0-9]{6}$/i}
	$C{colbg} ||='000000';
	$C{coltxt}||='FFFFFF';
	$C{collnk}||='6666FF';
	$C{colvis}||='FF66FF';
	$C{colact}||='FF0033';
	foreach(qw(sessionexpire guestsexpire messageexpire waitingexpire kickpenalty defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidthdef boxheightdef)){$C{$_}=~y/0-9//cd;$C{$_}=~s/^0+//}
	$C{sessionexpire} ||='15';
	$C{guestsexpire}  ||='10';
	$C{messageexpire} ||='10';
	$C{waitingexpire} ||='5';
	$C{kickpenalty}   ||='10';
	$C{defaultrefresh}||='20';
	$C{minrefresh}    ||='15';
	$C{maxrefresh}    ||='150';
	$C{maxmessage}    ||='1000';
	$C{maxname}       ||='20';
	$C{minpass}       ||='10';
	$C{floodlimit}    ||='1';
	$C{boxwidthdef}   ||='40';
	$C{boxheightdef}  ||='3';
	# Use language defaults if emptied
	$C{title}||='LE CHAT';
	foreach(qw(header footer noguests guestaccess loginbutton rulestxt links entrymessage logoutmessage kickederror roomentry roomexit regmessage kickedmessage roomclean nowchatting mesall mesmem mespm messtaff)){$C{$_}||=$I{"c$_"}}
	$C{framesizes}='100,*,80'if($C{framesizes}!~/^(?:\d+\%?|\*)\,(?:\d+\%?|\*)\,(?:\d+\%?|\*)$/);
}

sub set_config_defaults{
	# define keys
	%C=();foreach(qw(
		lastchangedby lastchangedat
		redirifsusp redirtourl
		createlinks linksswitch useextderef extderefurl allowmultiline allowfonts allowpms
		title favicon
		header footer noguests guestaccess loginbutton rulestxt links entrymessage logoutmessage kickederror roomentry roomexit regmessage kickedmessage roomclean nowchatting 
		mesall mesmem mespm messtaff
		textfilters
		rndguestcol sessionexpire guestsexpire messageexpire waitingexpire kickpenalty defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidthdef boxheightdef
		coltxt colbg collnk colvis colact
		cssglobal styleback cssview styledelsome stylecheckwait csswait stylewaitrel csspost styleposttext stylepostsend stylesendlist styledellast styledelall styleswitch csscontrols stylerelpost stylerelmes styleprofile styleadmin stylerules styleexit csslogin stylelogintext stylecolselect styleenter csserror cssprofile cssrules cssadmin tableattributes frameattributes framesizes 
	)){$C{$_}=''}
	# initial defaults
	$C{lastchangedby}='-';
	$C{lastchangedat}='-';
	$C{createlinks}='1';
	$C{linksswitch}='1';
	$C{allowmultiline}='1';
	$C{allowfonts}='1';
	$C{allowpms}='1';
	$C{rndguestcol}='1';
	$C{textfilters}=$I{ctextfilters};
	$C{favicon}='data:image/gif;base64,R0lGODlhEAAQALMAAP///wAAAEBAQICAgAAAgIAAgACAgMDAwICAgP8AAAD/AP//AAAA//8A/wD//////ywAAAAAEAAQAAAEPBAMQGW9dITB9cSVFoxBOH4SuWWbx5KTa5lrimKyDOp6KKK9FMx0Ew1ZF+Pp01PWmqoVpyaMHjOdbKcSAQA7';
	$C{cssglobal}="input,select,textarea{color:#FFFFFF;background-color:#000000;}\nbody{background-image:url(data:image/gif;base64,R0lGODdhCAAIALMAAAAAADMzMwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAACAAIAAAEChDISQO9OOu6dwQAOw==);}";
	$C{styleback}='background-color:#004400;color:#FFFFFF;';
	$C{styledelsome}='background-color:#660000;color:#FFFFFF;';
	$C{stylecheckwait}='background-color:#660000;color:#FFFFFF;';
	$C{stylecolselect}='text-align:center;';
	$C{csserror}='body{color:#FF0033;}';
	$C{tableattributes}='border="2" width="1" rules="none"';
	$C{frameattributes}='border="3" frameborder="3" framespacing="3"';
	# required defaults
	check_config();
}

sub set_internal_defaults{
	%F=(# fonts. TODO: review these and choose some cross-platform friendly items
		'Arial'          =>' face="Arial,Helvetica,sans-serif"',
		'Book Antiqua'   =>' face="Book Antiqua,MS Gothic"',
		'Comic'          =>' face="Comic Sans MS,Papyrus"', 
		'Comic small'    =>' face="Comic Sans MS,Papyrus" size="-1"',
		'Courier'        =>' face="Courier New,Courier,monospace"',
		'Cursive'        =>' face="Cursive,Papyrus"',
		'Fantasy'        =>' face="Fantasy,Futura,Papyrus"',
		'Garamond'       =>' face="Garamond,Palatino,serif"',
		'Georgia'        =>' face="Georgia,Times New Roman,Times,serif"',
		'Serif'          =>' face="MS Serif,New York,serif"',
		'System'         =>' face="System,Chicago,sans-serif"',
		'Times New Roman'=>' face="Times New Roman,Times,serif"',
		'Verdana'        =>' face="Verdana,Geneva,Arial,Helvetica,sans-serif"',
		'Verdana small'  =>' face="Verdana,Geneva,Arial,Helvetica,sans-serif" size="-1"'
	);
	# Load default internal messages from __DATA__
	my $start=tell(DATA);
	while(<DATA>){
		my($ikey,$ival)=$_=~/^([a-z_]+)\s*=(.+)/i;
		next unless $ikey;
		last if('stop_action'eq$ikey and $ival=~/-$Q{action}[0]-/);# only load what we need
		$I{$ikey}=$ival;
	}
	seek(DATA,$start,0);# rewind for second use
}

sub set_html_vars{
	%H=(# default HTML
		begin_html   =>qq|\n<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n<html>\n|,
		begin_frames =>qq|\n<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN" "http://www.w3.org/TR/html4/frameset.dtd">\n<html>\n|,
		begin_body   =>qq|\n<body bgcolor="#$C{colbg}" text="#$C{coltxt}" link="#$C{collnk}" alink="#$C{colact}" vlink="#$C{colvis}">\n|,
		encoding     =>'iso-8859-1',
			# Don't change the encoding or existing member passes with special characters will break! 
			# Maybe I'll finally switch to utf-8 in v2.0 and break support for legacy browsers.
			# The whole variety of encodings, especially with passwords, is a global nightmare already. :(
		end_body     =>"\n</body>",
		end_html     =>"\n</html>\n\n<!-- LE CHAT $version ($lastchanged) Original script available at: http://4fvfamdpoulu2nms.onion/lechat/ -->\n\n",
		form         =>qq|form action="$S" method="post" style="margin:0;padding:0;"|,
		add_css      =>'',
		versiontag   =>"<small>LE&nbsp;CHAT&nbsp;-&nbsp;$version</small>",
		);%H=(%H,
		meta_html    =>qq|\n<title>$C{title}</title>\n|.linkrel($C{favicon}).qq|<meta name="robots" content="noindex,nofollow">\n<meta http-equiv="Content-Type" content="text/html; charset=$H{encoding}">\n<meta http-equiv="Content-Language" content="$I{languagecode}">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="expires" content="0">|,
		backtologin  =>qq|<$H{form} target="_parent">|.submit($I{backtologin},qq| style="$C{styleback}"|).'</form>',
		backtochat   =>qq|<$H{form}>|.hidden('action','view').hidden('session',$Q{session}[0]).submit($I{backtochat},qq| style="$C{styleback}"|).'</form>',
		backtoprofile=>qq|<$H{form}>|.hidden('action','profile').hidden('session',$Q{session}[0]).submit($I{backtoprofile},qq| style="$C{styleback}"|).'</form>',
		backtosetup  =>qq|<$H{form}>|.hidden('action','setup').hidden('nick',$Q{nick}[0]).hidden('hexpass',$Q{hexpass}[0]||unpack('H*',$Q{pass}[0])).submit($I{backtosetup},qq| style="$C{styleback}"|).'</form>',
	);
	##############################################################
	# add banner killers and other corrections for known servers #
	# to be updated regularly...  tell me your favourite hosts!  #
	##############################################################
	if($ENV{SERVER_NAME}=~m/\.atpages\.jp$/){
		$H{add_css}.="div{display:none !important; max-width:0px; max-height:0px; overflow:hidden !important}\n";
		$H{begin_body}.='<div style="display:block !important; width:98%; height:98%; max-width:98%; max-height:98% ;position:absolute; top:1%; left:1%; z-index:1000; overflow:visible !important">';
		$H{end_body}='<noembed><noframes><xml><xmp>'.$H{end_body};
		foreach(qw(form backtologin backtochat backtoprofile backtosetup)){$H{$_}=~s/method="post"/method="get"/}# large IP-bans on POST requests
	}
	elsif($ENV{SERVER_NAME}=~m/\.tok2\.com$/){
		$H{begin_body}='<noembed><noframes><noscript><body></noscript></noframes></noembed>'.$H{begin_body};
		$H{end_body}='<noembed><noframes><noscript>'.$H{end_body};
		$ENV{REMOTE_ADDR}=$ENV{HTTP_X_FORWARDED_FOR}if($ENV{REMOTE_ADDR}eq$ENV{SERVER_ADDR}and$ENV{HTTP_X_FORWARDED_FOR});# fix for some misconfigured tok2-servers
	}
	elsif($ENV{SERVER_NAME}=~m/\.h(ut)?\d+?\.ru$/){
		$H{end_html}.='<div style="display:none"><noembed><xml><xmp>';
	}
	elsif($ENV{SERVER_NAME}=~m/\.fatal\.ru$/){
		$H{end_body}='<div style="display:none"><noembed><xml><xmp><!--'.$H{end_body};
	}
	elsif($ENV{SERVER_NAME}=~m/\.onion$/){
		$ENV{REMOTE_ADDR}=$I{unknownip};# there are no IPs in Torland ;)
	}
}

######################################################################
# cgi stuff
######################################################################
sub GetQuery{read(STDIN,my$q,$ENV{CONTENT_LENGTH}||0);QueryHash($q)}
sub GetParam{QueryHash($ENV{QUERY_STRING}||'')}
sub QueryHash{my($n,$v,%h);foreach(split(/&|;/,$_[0])){($n,$v)=split(/=/,$_);$v=~tr/+/ /;$v=~s/%([\dA-Fa-f]{2})/pack('C',hex($1))/eg;$h{$n}||=[];push@{$h{$n}},$v}return%h}
sub GetScript{$0=~/([^\\\/]+)$/;$1||die}
######################################################################
# Internal messages. Don't edit here, use the setup-page as superuser
# and create a language file. If you want to share, send me a copy!
######################################################################
__DATA__
languagename=English
languagecode=en-gb
# login page
nickname     =Nickname:
password     =Password:
nickhelp     =4 characters minimun, <MAX> characters maximum, no special characters allowed
passhelp     =at least <MIN> characters required
selcolguests =Guests, choose a good password and a colour:
selcoldefault=Room Default
selcolrandom =Random Colour
unknownip    =not available
# colour names
Beige      =beige
Black      =black
Blue       =blue
BlueViolet =blue violet
Brown      =brown
Cyan       =cyan
DarkBlue   =dark blue
DarkGreen  =dark green
DarkRed    =dark red
DarkViolet =dark violet
DeepSkyBlue=sky blue
Gold       =gold
Grey       =grey
Green      =green
HotPink    =hot pink
Indigo     =indigo
LightBlue  =light blue
LightGreen =light green
LimeGreen  =lime green
Magenta    =magenta
Olive      =olive
Orange     =orange
OrangeRed  =orange red
Purple     =purple
Red        =red
RoyalBlue  =royal blue
SeaGreen   =sea green
Sienna     =sienna
Silver     =silver
Tan        =tan
Teal       =teal
Violet     =violet
White      =white
Yellow     =yellow
YellowGreen=yellow green
# link redirects
linkredirect=Redirecting to:
linknonhttp =Non-http link requested:
linktryhttp =Try link as http:
errnolinks  =Link redirection is disabled.
# suspended page
suspended=Suspended
susptext =This chat is currently not available. Please try again later!
redirtext=Please try this alternate address!
# error messages
fatalerror  =Fatal Error!
error       =Error:
errfile     =file error
errexpired  =invalid/expired session
erraccdenied=access denied
errnoguests =no guests allowed at this time
backtologin =Back to the login page.
# messages frame
members     =Members:
guests      =Guests:
butcheckwait=Check <COUNT> Newcomer(s)
navbot      =bottom
navtop      =top
# config default text
cheader       =<h1>LE CHAT</h1>Your IP address is <IP><br><br>
cfooter       =<br><VER>
cnoguests     =Only members at this time!
cloginbutton  =Enter LE CHAT
crulestxt     =Just be nice!
clinks	      =You can change or turn off the links in settings.
centrymessage =Welcome <NICK> to LE CHAT
clogoutmessage=Bye <NICK>, visit again soon!
ckickederror  =<NICK>, you have been kicked out of LE CHAT!
croomentry    =<NICK> enters LE CHAT!
croomexit     =<NICK> leaves LE CHAT.
cregmessage   =<NICK> is now a registered member of LE CHAT.
ckickedmessage=<NICK> has been kicked out of LE CHAT!
croomclean    =Messages have been cleaned.
cnowchatting  =Currently <COUNT> chatter(s) in room:<br><NAMES>
cmesall       =<NICK> &#62;&nbsp;
cmesmem       =<NICK> &#62;&#62;&nbsp;
cmespm        =<font color="white">[PM to <RECP>]</font> <NICK> &#62;&#62;&nbsp;
cmesstaff     =<font color="white">[Staff]</font> <NICK> &#62;&#62;&nbsp;
ctextfilters  =1"fuck"1"***BEEEP!!!***"1<>2"http(s?)://"1"hxxp$1://"1
stop_action=--view-redirect-
# post box frame
butsendto    =talk to
seltoall     =all chatters
seltomem     =members only
seltoadm     =staff only
butdellast   =Delete last message
butdelall    =Delete all messages
butmultiline =Switch to multi line
butsingleline=Switch to single line
kickfilter   =<NICK> has triggered an autokick filter!
butupload    =Uploader
stop_action=-post-delete-
# waiting room
waitroom   =Waiting Room
waitmessage=Welcome <NICK>, you are currently in the waiting room. Please be patient until an admin will let you into the chat room.<br><br>If this page doesn't refresh every <REFRESH> seconds, use the button below to reload it manually!
butreloadw =Reload Page
# various occasions
backtochat =Back to the chat.
savechanges=save changes
# error messages
errbadnick  =invalid nickname (<MAX> characters max, 4 characters min, no special characters allowed, and name needs to make sense)
errnonick   =No nickname given.
errexistnick=Nick exists already.
erraccdenied=access denied
errbadpass  =invalid password (at least <MIN> characters required)
errbadlogin =invalid nickname/password
# entry page
entryhelp=If this frame does not reload in <REFRESH> seconds, you'll have to enable automatic redirection (meta refresh) in your browser. Also make sure no web filter, local proxy tool or browser plugin is preventing automatic refreshing! This could be for example "Polipo", "NoScript", "TorButton", "Proxomitron", etc. just to name a few.<br>As a workaround (or in case of server/proxy reload errors) you can always use the buttons at the bottom to refresh manually.
frames   =This chat uses <b>frames</b>. Please enable frames in your browser or use a suitable one!
stop_action=-wait-login-entry-logout-
# controls frame
butreloadp=Reload Post Box
butreloadm=Reload Messages
butprofile=Change Profile
butadmin  =Admin
butrules  =Rules &#38; Help
butlinks  =Links
butexit   =Exit Chat
stop_action=-controls-
# profile page
profileheader=Your Profile
refreshrate  =Refresh rate (<MIN>-<MAX> seconds)
entryrefresh =Entry page delay (1-<DEFAULT> seconds)
fontcolour   =Font colour
viewcolours  =view examples
fontface     =Font face
fontdefault  =Room Default
fontbold     =bold
fontitalic   =italic
fontexample  =example for your chosen font
boxsizes     =Post box size
boxwidth     =width:
boxheight    =height:
changepass   =Change Password
oldpass      =old password:
newpass      =new password:
confirmpass  =confirm new password:
succchanged  =Your profile was successfully saved.
errdiffpass  =Password confirmation does not match.
errwrongpass =Password is wrong.
# colourtable
colheader    =Colourtable
backtoprofile=Back to your profile.
stop_action=-profile-colours-
# rules and help page
rules     =Rules
help      =Help
helpguests=<b>Make sure you read the rules.</b> All functions are the same as every other LE CHAT. Just use the buttons. In your profile you can adjust the refresh rate, font colour and your preferred input box size.<br><u>Note:</u> This is a chat, so if you don't keep talking, you will be automatically logged out after a certain amount of time.<p>In this chat you can use Emojicons to express yourself. All you need to do is type the emoji name in between two :: Giving an example, if you wanted to do the "inlove" emoji you would type :inlove: where you wanted the emoji to go. "I was so :inlove:" <p>The list of emojis are: afk angel animated-hearts areyouthere askeye bang-your-head bat beer biker blow-kiss blush brb bye callyou castaway chicken circle-of-hearts club-me danceban dancing dracula drool dunno eyes finger flamming giveup goodjob googly-eyes greetings heart heart-wings hmm holdon imw inlove insane joint lightbulb likeavirgin lol lurk mallet mob ninja no omfg party popcorn puppybark right_on rip rofl rules sealed-shut shock shock2 shy sign_pervert sleep smile snowman spinning star sunflower swirl swirlcolor taunt teddy waiting wakka wave waytogo welcome whacky why yes
helpregs  =<p></p><b>Members:</b> You'll have some more options in your profile. You can adjust your font face and you can change your password anytime. You also don't need to type the capcha when loggin in, just your password would do. 
helpmods  =<b>Moderators:</b> Notice the Admin-button at the bottom. It'll bring up a page where you can clean the room, kick chatters, view all active sessions and disable guest access completely if needed. To moderate please use the admin panel or type the needed command in the post box: <p></p>To clean the room text: /clean room <p></p> To kick a user: /kick [reasonforkick]@[username] <p>Use the /name [username] command to ban user names from the chat.<p></p> To completely clear users messages: /delmess [username] <p></p> To logout user: /logout [username].
helpadmins=<b>Admins:</b> You'll be furthermore able to register guests, edit members and register new nicks without them being in the room.
stop_action=-help-
# admin waiting room/sessions
admwaiting  =Guests in Waiting Room
admsessions =Active Sessions
nicklist    =Nickname
timeoutin   =Timeout&nbsp;in
ip          =IP-Number
useragent   =Browser-Identification
allowchecked=allow checked
allowall    =allow all
denychecked =deny checked
denyall     =deny all
denymessage =Send message to denied:
butallowdeny=allow/deny
waitempty   =No more entry requests to approve.
# admin page
admheader     =Administrative Functions
admclean      =Clean Messages
admcleanall   =whole room
admcleansome  =selection
butdelsome    =delete selected messages
admkick       =Kick Chatter (<KICK> minutes)
admkickmes    =Send hint:
admkickpurge  =also purge messages
adminactive   =Logout Inactive Chatter
admvsessions  =View Active Sessions
admguests     =Guest Access
admguestsoff  =always forbid
admguestson   =always allow
admguestsauto =allow while an admin is present
admguestsmod  =allow while an mod is present
admguestsbell =require admin approval for entry
admregguest   =Register Guest
admmembers    =Members
admregnew     =Register New Member
selmemdelete  =delete from file
selmemdeny    =deny access
selmemreg     =set to regular
selmemmod     =set to moderator
selmemadmin   =set to admin
selchoose     =(choose)
symdenied     =(!)
symguest      =(G)
symmod        =(M)
symadmin      =(A)
butadmclean   =clean
butadmkick    =kick
butadminactive=logout
butadmview    =view
butadmset     =set
butadmreg     =register
butadmstatus  =change
butadmregnew  =register
# admin messages
succreg      ="<NICK>" successfully registered.
succstatus   =Status of "<NICK>" successfully changed.
succdelmem   ="<NICK>" successfully deleted from file.
errcantreg   =cannot register "<NICK>"
errcantregnew=cannot register new member "<NICK>"
errcantkick  =cannot kick "<NICK>"
errcantlogout=cannot logout "<NICK>"
erralreadyreg="<NICK>" is already registered.
errcantstatus=cannot change status of "<NICK>"
stop_action=-admin-
# setup login
aloginname=Name:
aloginpass=Pass:
aloginbut =login
# descriptions on setup page
chatsetup    =Chat Setup
chataccess   =Chat Access
suspend      =suspended
enabled      =enabled
derefonly    =link redirection only
butset       =set
backups      =Backups
backmem      =backup members
backcfg      =backup configuration
restore      =restore backup
backdat      =Backup data to copy/paste.
mainadmins   =Main Admins
regadmin     =Register new Main Admin
raiseadmin   =Raise to Main Admin
loweradmin   =Lower to Regular Admin
butregadmin  =register
butraise     =raise
butlower     =lower
cfglanguage  =Language Settings
editlanguage =create/edit language files
resetlanguage=reset language to the default (english)
cfgsettings  =Change Configuration Settings
cfgmainadm   =Log in with your main admin nick instead of the superuser to change particular chat settings!
butlogout    =log out
lastchanged  =Last changed:
# redirection
redirifsusp  =Redirect to alternate URL if suspended
redirtourl   =Redirection URL
# auto hotlinks
createlinks  =Create hotlinks from URLs
useextderef  =Use external link redirection script
extderefurl  =External link redirection script URL
# options
allowfonts     =Allow change of font face
allowmultiline =Allow multiline messages
allowpms       =Allow private messages
rndguestcol    =Randomise default colour for guests
yes            =yes
no             =no
# text filters
filterslist    =Content filters
filtersnew     =Add new filter
factive        =Filter is active.
fdisabled      =Filter is disabled.
fdelete        =Delete this filter!
fregexerror    =Regular expression contains errors!
fchoosetype    =(choose filter type)
ftypetext      =Find exact words (separated by "|"):
ftyperegex     =Match regular expression:
fchooseaction  =(choose filter action)
factionreplace =Replace matched text with:
factionkick    =Kick chatter, replace text with:
factionpurge   =Kick, purge and send message:
fseparator     =------------------------------------------------------------
# values
sessionexpire  =Minutes of silence until member session expires
guestsexpire   =Minutes of silence until guest session expires
messageexpire  =Minutes until messages get removed
kickpenalty    =Minutes nickname is blocked after beeing kicked
waitingexpire  =Minutes until guest entry requests expire
defaultrefresh =Default refresh time (seconds)
minrefresh     =Minimum refresh time (seconds)
maxrefresh     =Maximum refresh time (seconds)
floodlimit     =Minimum time between posts from same nick (seconds)
boxwidthdef    =Default post box width
boxheightdef   =Default post box height
maxmessage     =Maximum message length
maxname        =Maximum characters for nickname
minpass        =Minimum characters for password
# text
title          =Browser title / name of the chat
favicon        =Browser icon URL (favicon)
noguests       =Text if no guests allowed
loginbutton    =Login button text
header         =Login page header (&#60;IP&#62;=users IP-address, &#60;VER&#62;=version)
footer         =Login page footer (&#60;IP&#62;=users IP-address, &#60;VER&#62;=version)
rulestxt       =Rules (&#60;IP&#62; shows users IP-address)
links	       =Links (html links are supported)
linksswitch    =Show the links button
nowchatting    =Now chatting (&#60;NAMES&#62;=list, &#60;COUNT&#62;=number)
entrymessage   =Entry message (use &#60;NICK&#62; for name)
logoutmessage  =Logout message (use &#60;NICK&#62; for name)
kickederror    =Kicked error message (use &#60;NICK&#62; for name)
roomentry      =Entry notification (use &#60;NICK&#62; for name)
roomexit       =Exit notification (use &#60;NICK&#62; for name)
regmessage     =Register notification (use &#60;NICK&#62; for name)
kickedmessage  =Kick notification (use &#60;NICK&#62; for name)
roomclean      =Cleaning message
# message enclosures
mesall         =Message to all (use &#60;NICK&#62; for name)
mesmem         =Message to members (use &#60;NICK&#62; for name)
mespm          =Private Messages (&#60;NICK&#62;=poster, &#60;RECP&#62;=recipient)
messtaff       =Staff Messages (use &#60;NICK&#62; for name)
# default colors for body and non-CSS browsers
colbg          =Background colour
coltxt         =Text colour
collnk         =Link colour
colvis         =Visited link colour
colact         =Active link colour
# styles
cssglobal      =CSS for all pages
styleback      =back button style
csslogin       =CSS login page
stylelogintext =textfield style
stylecolselect =selection style
styleenter     =login button style
csspost        =CSS post frame
styleposttext  =post text style
stylepostsend  =talk to button style
stylesendlist  =send list style
styledellast   =delete last button style
styledelall    =delete all button style
styleswitch    =multiline button style
cssview        =CSS messages frame
styledelsome   =delete selected button style
stylecheckwait =check newcomers button style
csswait        =CSS waiting room
stylewaitrel   =reload button style
csscontrols    =CSS controls frame
stylerelpost   =reload post box button style
stylerelmes    =reload messages button style
styleprofile   =profile button style
styleadmin     =admin button style
stylerules     =rules button style
styleexit      =exit button style
cssprofile     =CSS profile page
cssrules       =CSS rules page
cssadmin       =CSS admin pages
csserror       =CSS error pages
# layout
tableattributes=table attributes login page
frameattributes=frame attributes
framesizes     =frame sizes
# initialisation stuff
invalidbackup =No valid backup data given.
membrestfail  =Restoring members failed:
membrestsucc  =Restoring members succeeded.
membrestinval =Invalid data for members file.
confrestfail  =Restoring configuration failed:
confrestsucc  =Restoring configuration succeeded.
confrestinval =Invalid data for configuration file.
langrestfail  =Restoring language failed:
langrestsucc  =Restoring language succeeded.
langrestinval =Invalid data for language file.
raisemainsucc ="<NICK>" raised to main admin.
raisemaindone ="<NICK>" is already main admin.
raisemainfail ="<NICK>" is not an admin.
lowerregsucc  ="<NICK>" lowered to regular admin.
lowerregdone  ="<NICK>" is already regular admin.
lowerregfail  ="<NICK>" is not an admin.
newmainreg    =New main admin "<NICK>" registered.
errbaddata    =Invalid data received.
initsetup     =Initial Setup
setsu         =Superuser Login
setsunick     =Superuser nickname:
setsupass     =Superuser password:
setsupassconf =Confirm password:
setsuhelp     =In case of file corruption on the server, you can still restore backups with your superuser nick. You will also need it to install main admins who will be able to make changes to the chat setup, suspend/unsuspend the chat and upgrade members to moderators and regular admins.<br>You can not alter your superuser login later, so choose a secret nick and a very strong pass here. Take a nick that will not show up in the chat room. If you ever need to reset the superuser, you will have to delete the file "<DATA>/admin" on the server and do this setup here again.
initback      =Restore Backups
initbackhelp  =If you want to recover files (members, config, language) from existing backup data, paste it all here:
initbut       =initialise chat
suerrfileexist=A superuser file exists already!
suerrbadnick  =Invalid nickname for superuser (<MAX> characters maximum, no special characters allowed). Try again!
suerrbadpass  =Password too short, <MIN> characters required. Try again!
suerrbadpassc =Password confirmation does not match. Try again!
suwritesucc   =Superuser file was written successfully.
suwritefail   =Superuser file was not written correctly. Please try again!<br><br>(If this error persists, make sure the script is allowed to create files and folders. Possibly you may have to create the data folder manually first.)
initgotosetup =Go to the Setup-Page.
initlechattxt =Results of lechat.txt:
# language editing
lngheader  =Language File Editor
lnghelp    =Fill in your translations below the original texts and save your changes. Use the corresponding HTML entities to display special characters! (&nbsp;'&#38;'&nbsp;=&nbsp;'&#38;#38;'&nbsp;, '&#60;'&nbsp;=&nbsp;'&#38;#60;'&nbsp;, '&#62;'&nbsp;=&nbsp;'&#38;#62;'&nbsp;)<br>To apply your edits to the chat, create a backup here and restore that on the setup page. For empty entries, the english defaults will be used.
lngload    =restore language data from backup
lngbackup  =create backup from saved data
lngtoken   =Token
lngdeftxt  =Default Text
backtosetup=Back to the Setup-Page.
