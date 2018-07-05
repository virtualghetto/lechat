#!/usr/bin/perl

q/
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#    #      #####        ####  #   #   ###   #####      /\_/\       #
#    #      #           #      #   #  #   #    #       ( o.o )      #
#    #      ###         #      #####  #####    #        > ^ <       #
#    #      #           #      #   #  #   #    #        v1.13       #
#    #####  #####        ####  #   #  #   #    #      2012-09-06    #
#                                                                   #
#  Installation instructions:                                       #
#                                                                   #
#  Upload this file into your cgi-bin directory (you can rename it  #
#  to whatever  you want,  if you prefer)  and make it  executable  #
#  (chmod 711).  If you have language data or backups  you want to  #
#  restore initially,  you can  put that all in  a textfile  named  #
#  "lechat.txt" and put it next to your script file on the server.  #
#  Then call the script in your browser with parameter like this:   #
#                                                                   #
#  http://(server)/(cgi-path)/(script-name).cgi?action=setup        #
#                                                                   #
#  All necessary installation settings can be made from there.      #
#  The server needs to support Perl CGI scripts, obviously.         #
#                                                                   #
#  This script comes without any warranties. Use at your own risk,  #
#  don't  blame me for modifications you make.  Verify my attached  #
#  PGP-signature,  to make sure  you got  the original  and not an  #
#  altered copy! Really, do verify it!                              #
#  If you spread the script, please only give away the original!    #
#                                                                   #
#  I wrote the script from scratch and all the code is my own, but  #
#  as you may notice,  I took some ideas  from other scripts  that  #
#  are out there. Bug reports and feedback are very welcome.        #
#  Banner killers for known hosts are built in, please report back  #
#  any problems there or any other hosts you are using!             #
#  If you want to help out with translations and create further     #
#  language files, then please contact me!                          #
#                                                                   #
#  The "LE" in the name  you can take as  "Lucky Eddie",  or since  #
#  the script was meant to be lean and easy on server resources,    #
#  as "Light Edition". It may even be the french word for "the" if  #
#  you prefer. Translated from french to english, "le chat" means:  #
#  "the cat".                                                       #
#                                                                   #
#  Other than that, enjoy! ;)                                       #
#                                                                   #
#  Lucky Eddie                                                      #
#                                                                   #
####################################################################/
;
use strict;
use Fcntl qw(:DEFAULT :flock);

######################################################################
# Data directory, could be changed, but shouldn't be necessary
######################################################################
my $datadir='./lcdat';

######################################################################
# No need to change anything below. Always use: *.cgi?action=setup
######################################################################
my($version,$lastchanged)=('v1.13','2012-09-06');
my($S,%Q)=(&GetScript(),&GetQuery(),&GetParam());
my $guests=get_guests_access();# guest settings
my $admincount=0;# number of admins in room
my %U;# this user data
my %X;# all present users (nick=>[hex,status,style])
my %A;# All registered members (nick=>[hex,status,style])
my @M;# Members: display names
my @G;# Guests: display names
my %F;# fonts
my %C;# configuration
my %I;# internal texts and error messages
my %H;# HTML-stuff
load_config();

######################################################################
# main program: decide what to do based on queries
######################################################################
print "Content-Type: text/html; charset=$I{charset}\nPragma: no-cache\nExpires: 0\n";

if($Q{action}[0]eq'setup'){
	send_init() unless -e"$datadir/admin";
	send_alogin() unless valid_admin($Q{name}[0],$Q{pass}[0]);
	if($Q{do}[0]eq'config'){
		set_config();
		save_config();
	}elsif($Q{do}[0]eq'chataccess'){ 
		if($Q{set}[0]eq'off'){
			suspend_chat();
		}elsif($Q{set}[0]eq'on'){
			unsuspend_chat();
		}
	}elsif($Q{do}[0]eq'backup'){
		$I{backdat}=get_members_backup() if $Q{what}[0]eq'members';
		$I{backdat}=get_config_backup() if $Q{what}[0]eq'config';
	}elsif($Q{do}[0]eq'restore'){
		$I{backdat}=get_restore_results();
	}elsif($Q{do}[0]eq'mainadmin'and$U{status}==9){
		send_setup(change_admin_status());
	}elsif($Q{do}[0]eq'resetlanguage'and$U{status}==9){
		unlink("$datadir/language");
		load_config();
	}
	send_setup();
}
elsif($Q{action}[0]eq'init' and !-e"$datadir/admin"){
	init_chat();
}
elsif(!-e"$datadir/opened"){
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
		update_sessions();
		validate_input();
		add_message();
	}
	send_post();
}
elsif($Q{action}[0]eq'delete'){
	check_session();
	del_all_messages() if $Q{what}[0]eq'all';
	del_last_message() if $Q{what}[0]eq'last';
	send_post();
}
elsif($Q{action}[0]eq'login'){
	create_session();
	send_frameset();
}
elsif($Q{action}[0]eq'controls'){
	check_session();
	send_controls();
}
elsif($Q{action}[0]eq'profile'){
	check_session();
	save_profile() if $Q{do}[0]eq'save';
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
elsif($Q{action}[0]eq'admin'){
	check_session();
	send_login() unless $U{status}>=6;
	if($Q{do}[0]eq'clean'){
		send_choose_messages() if $Q{what}[0]eq'choose';
		clean_selected() if $Q{what}[0]eq'selected';
		clean_room() if $Q{what}[0]eq'room';
		send_messages();
	}
	elsif($Q{do}[0]eq'sessions'){
		send_sessions();
	}
	elsif($Q{do}[0]eq'kick'){
		kick_chatter();
		del_all_messages(pack('H*',$Q{name}[0])) if $Q{what}[0]eq'purge';
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'guests'){
		set_guests_access($Q{set}[0]) if($U{status}>=7 or $Q{set}[0]==0);
	}
	elsif($Q{do}[0]eq'register'){
		register_guest();
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'regnew'){
		register_new();
	}
	elsif($Q{do}[0]eq'status'){
		change_status();
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

sub send_alogin{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	print qq|</head>$H{begin_body}<center><table><form action="$S" method="post"><input type="hidden" name="action" value="setup"><tr><td>$I{aloginname}</td><td><input type="text" name="name" size="15"></td></tr><tr><td>$I{aloginpass}</td><td><input type="password" name="pass" size="15"></td></tr><tr><td colspan="2" align="right"><input type="submit" value="$I{aloginbut}"></td></tr></table></center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_setup{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	foreach(keys %C){
		$C{$_}=~s/&/&amp;/g;
		$C{$_}=~s/"/&quot;/g;
		$C{$_}=~s/</&lt;/g;
		$C{$_}=~s/>/&gt;/g;
	}
	print qq|</head>$H{begin_body}<center><h2>$I{chatsetup}</h2><table>|,frmset('chataccess'),qq|<td align="left"><b>$I{chataccess}&nbsp;</b></td><td align="right"><input type="radio" name="set" id="off" value="off"|;
	print ' checked' unless -e"$datadir/opened";
	print qq|><label for="off">&nbsp;$I{suspend}</label>&nbsp;&nbsp;<input type="radio" name="set" id="on" value="on"|;
	print ' checked' if -e"$datadir/opened";
	print qq|><label for="on">&nbsp;$I{enabled}</label>&nbsp;&nbsp;</td><td align="right"><input type="submit" value="$I{butset}"></td></form></table><br><h2>$I{backups}</h2><table><tr><td align="left"><table><tr>|;
	print frmset('backup','members'),qq|<td><input type="submit" value="$I{backmem}"></td><td>&dArr;&nbsp;</td></form>|,
		frmset('backup','config'),qq|<td><input type="submit" value="$I{backcfg}"></td><td>&dArr;&nbsp;</td></form></td></tr></table></td></tr>|,
		frmset('restore'),qq|<tr><td align="center"><textarea name="backupdata" rows="8" cols="80" wrap="off">$I{backdat}</textarea></td></tr><tr><td align="right">&rArr;&nbsp;<input type="submit" value="$I{restore}"></td></tr></form></table><br>|;
	if($U{status}==9){
		print qq|<h2>$I{mainadmins}</h2><i>$_[0]</i><table border="0">|,thr(3),qq|<tr><td colspan="3" align="left"><b>$I{regadmin}</b></td></tr><tr>|,frmset('mainadmin','new'),qq|<td align="right" colspan="2">$I{nickname}&nbsp;<input type="text" name="admnick" size="20" maxlength="$C{maxname}"></td><td>&nbsp;</td></tr><tr><td align="right" colspan="2">$I{password}&nbsp;<input type="text" name="admpass" size="20"></td><td align="right"><input type="submit" value="$I{butregadmin}"></td></form>|,
			qq|</tr>|,thr(3),qq|<tr><td align="left"><b>$I{raiseadmin}</b></td>|,frmset('mainadmin','up'),qq|<td align="right">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<select name="admnick" size="1"><option value="">$I{selchoose}</option>|;
		print_memberslist(7);
		print qq|</select></td><td align="right"><input type="submit" value="$I{butraise}"></td></form></tr>|,thr(3),qq|<tr><td align="left"><b>$I{loweradmin}</b></td>|,frmset('mainadmin','down'),qq|<td align="right">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<select name="admnick" size="1"><option value="">$I{selchoose}</option>|;
		print_memberslist(8);
		print qq|</select></td><td align="right"><input type="submit" value="$I{butlower}"></td></form></tr>|,thr(3),qq|</table><br><br><h2>$I{cfgsettings}</h2>|;
		print frmset('resetlanguage'),qq|<input type="submit" value="$I{resetlanguage}"></form><br><br>|if(-e"$datadir/language");
		print qq|$I{cfgmainadm}<br><br>|;
	}else{
		print qq|<h2>$I{cfgsettings}</h2>\n<table>\n<form action="$S" method="post">\n<input type="hidden" name="action" value="setup">\n<input type="hidden" name="do" value="config">\n<input type="hidden" name="name" value="$Q{name}[0]">\n<input type="hidden" name="pass" value="$Q{pass}[0]">|;
		print thr(2),cfgyn('redirifsusp'),cfgtm('redirtourl'),thr(2),cfgyn('allowfonts'),cfgyn('allowmultiline'),cfgyn('allowpms'),cfgyn('rndguestcol'),thr(2),cfgts('sessionexpire'),cfgts('guestsexpire'),cfgts('messageexpire'),cfgts('kickpenalty'),cfgts('waitingexpire'),thr(2),cfgts('defaultrefresh'),cfgts('minrefresh'),cfgts('maxrefresh'),cfgts('floodlimit'),thr(2),
			cfgts('boxwidthdef'),cfgts('boxheightdef'),cfgts('maxmessage'),cfgts('maxname'),cfgts('minpass'),thr(2),cfgtm('title'),cfgtm('noguests'),cfgtm('loginbutton'),thr(2),cfgta('header'),cfgta('footer'),thr(2),cfgta('rulestxt'),thr(2),cfgtb('nowchatting'),thr(2),cfgtb('entrymessage'),cfgtb('logoutmessage'),cfgtb('kickederror'),thr(2),
			cfgtb('roomentry'),cfgtb('roomexit'),cfgtb('regmessage'),cfgtb('kickedmessage'),cfgtb('roomclean'),thr(2),cfgtb('mesall'),cfgtb('mesmem'),cfgtb('messtaff'),cfgtb('mespm'),thr(2),cfgts('colbg'),cfgts('coltxt'),cfgts('collnk'),cfgts('colvis'),cfgts('colact'),thr(2),
			cfgta('cssglobal'),cfgtb('styleback'),thr(2),cfgta('csslogin'),cfgtb('stylelogintext'),cfgtb('stylecolselect'),cfgtb('styleenter'),thr(2),cfgta('csspost'),cfgtb('styleposttext'),cfgtb('stylepostsend'),cfgtb('stylesendlist'),cfgtb('styledellast'),cfgtb('styledelall'),cfgtb('styleswitch'),thr(2),
			cfgta('cssview'),cfgtb('styledelsome'),cfgtb('stylecheckwait'),thr(2),cfgta('csswait'),cfgtb('stylewaitrel'),thr(2),cfgta('csscontrols'),cfgtb('stylerelpost'),cfgtb('stylerelmes'),cfgtb('styleprofile'),cfgtb('styleadmin'),cfgtb('stylerules'),cfgtb('styleexit'),thr(2),
			cfgta('cssprofile'),thr(2),cfgta('cssadmin'),thr(2),cfgta('csserror'),thr(2),cfgtb('tableattributes'),cfgtb('frameattributes'),thr(2);
		print qq|<tr><td colspan="2" align="center"><small>$I{lastchanged} $C{lastchangedat}/$C{lastchangedby}</small><br><br></td></tr><tr><td colspan="2" align="center"><input type="submit" value="$I{butsavecfg}"></td></tr></form></table><br>|;
	}
	print qq|<form action="$S" method="post"><input type="hidden" name="action" value="setup"><table><tr><td><input type="submit" value="$I{butlogout}"></td></tr></table></form><small>LE&nbsp;CHAT&nbsp;-&nbsp;$version</small></center>$H{end_body}$H{end_html}|;
	exit;
}

sub frmset{qq|<form action="$S" method="post"><input type="hidden" name="action" value="setup"><input type="hidden" name="name" value="$Q{name}[0]"><input type="hidden" name="pass" value="$Q{pass}[0]">|.($_[0]?qq|<input type="hidden" name="do" value="$_[0]">|:'').($_[1]?qq|<input type="hidden" name="what" value="$_[1]">|:'')}
sub frmadm{qq|<form action="$S" method="post" target="view"><input type="hidden" name="action" value="admin"><input type="hidden" name="do" value="$_[0]"><input type="hidden" name="session" value="$U{session}">|}
sub thr{qq|<tr><td colspan="$_[0]"><hr></td></tr>|}
sub cfgyn{qq|<tr><td>$I{$_[0]}</td><td align="right"><input type="radio" name="$_[0]" id="$_[0]1" value="1"|.($C{$_[0]}?' checked':'').qq|><label for="$_[0]1">&nbsp;$I{yes}</label>&nbsp;&nbsp;&nbsp;<input type="radio" name="$_[0]" id="$_[0]0" value="0"|.($C{$_[0]}?'':' checked').qq|><label for="$_[0]0">&nbsp;$I{no}</label></td></tr>|}
sub cfgts{qq|<tr><td>$I{$_[0]}</td><td align="right"><input type="text" name="$_[0]" value="$C{$_[0]}" size="7" maxlength="6"></td></tr>|}
sub cfgtm{qq|<tr><td>$I{$_[0]}</td><td align="right"><input type="text" name="$_[0]" value="$C{$_[0]}" size="30"></td></tr>|}
sub cfgtb{qq|<tr><td>$I{$_[0]}</td><td align="right"><input type="text" name="$_[0]" value="$C{$_[0]}" size="50"></td></tr>|}
sub cfgta{qq|<tr><td valign="top">$I{$_[0]}</td><td align="right"><textarea name="$_[0]" rows="4" cols="40" wrap="off">$C{$_[0]}</textarea></td></tr>|}

sub send_admin{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	print qq|</head>$H{begin_body}<center><h2>$I{admheader}</h2><i>$_[0]</i><table border="0">|,thr(3),
		frmadm('clean'),qq|<tr><td align="left"><b>$I{admclean}</b></td><td align="right">&nbsp;&nbsp;&nbsp;<nobr><input type="radio" name="what" id="room" value="room"><label for="room">&nbsp;$I{admcleanall}</label></nobr>&nbsp;&nbsp;&nbsp;<nobr><input type="radio" name="what" id="choose" value="choose" checked><label for="choose">&nbsp;$I{admcleansome}</label></nobr>&nbsp;</td><td align="right"><input type="submit" value="$I{butadmclean}"></td></tr></form>|,thr(3),
		frmadm('kick'),qq|<tr><td align="left" colspan="3"><b>$I{admkick}</b> ($C{kickpenalty} $I{minutes})</td></tr><tr><td align="right" colspan="2"><input type="checkbox" name="what" value="purge" id="purge"><label for="purge">&nbsp;$I{admkickpurge}</label>&nbsp;&nbsp;&nbsp;<select name="name" size="1"><option value="">$I{selchoose}</option>|;
	foreach(sort {lc($a) cmp lc($b)} keys %X){print '<option value="',$X{$_}[0],'" style="',$X{$_}[2],'">',$_,'</option>'if($X{$_}[1]>0 and $X{$_}[1]<$U{status})}
	print qq|</select></td><td align="right"><input type="submit" value="$I{butadmkick}"></td></form></tr>|,thr(3),
		frmadm('sessions'),qq|<tr><td align="left" colspan="2"><b>$I{admvsessions}</b></td><td align="right"><input type="submit" value="$I{butadmview}"></td></form></tr>|,thr(3),
		frmadm('guests'),qq|<tr><td align="left" colspan="3"><b>$I{admguests}</b></td></tr><tr><td align="left" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="set" id="set0" value="0"|;
	print ' checked' if $guests==0;
	print qq|><label for="set0">&nbsp;$I{admguestsoff}</label></td><td>&nbsp;</td></tr><tr><td align="left" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="set" id="set1" value="1"|;
	print ' disabled' unless $U{status}>=7;
	print ' checked' if $guests==1;
	print qq|><label for="set1">&nbsp;$I{admguestson}</label></td><td>&nbsp;</td></tr><tr><td align="left" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="set" id="set2" value="2"|;
	print ' disabled' unless $U{status}>=7;
	print ' checked' if $guests==2;
	print qq|><label for="set2">&nbsp;$I{admguestsauto}</label></td><td>&nbsp;</td></tr><tr><td align="left" colspan="2">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="set" id="set3" value="3"|;
	print ' disabled' unless $U{status}>=7;
	print ' checked' if $guests==3;
	print qq|><label for="set3">&nbsp;$I{admguestsbell}</label></td><td align="right"><input type="submit" value="$I{butadmset}"></td></tr></form>|,thr(3);
	if($U{status}>=7){
		print frmadm('register'),qq|<tr><td align="left"><b>$I{admregguest}</b></td><td align="right"><select name="name" size="1"><option value="">$I{selchoose}</option>|;
		foreach(sort {lc($a) cmp lc($b)} keys %X){print '<option value="',$X{$_}[0],'" style="',$X{$_}[2],'">',$_,'</option>'if $X{$_}[1]==1} 
		print qq|</select></td><td align="right"><input type="submit" value="$I{butadmreg}"></td></form></tr>|,thr(3),qq|<tr><td colspan="3" align="left"><b>$I{admmembers}</b></td></tr>|,frmadm('status'),qq|<tr><td align="right" colspan="2"><select name="name" size="1"><option value="">$I{selchoose}</option>|;
		print_memberslist();
		print qq|</select>&nbsp;<select name="set" size="1"><option value="">$I{selchoose}</option><option value="-">$I{selmemdelete}</option><option value="0">$I{selmemdeny} $I{symdenied}</option><option value="2">$I{selmemreg}</option><option value="6">$I{selmemmod} $I{symmod}</option>|;
		print qq|<option value="7">$I{selmemadmin} $I{symadmin}</option>|if($U{status}==8);
		print qq|</select></td><td align="right"><input type="submit" value="$I{butadmstatus}"></td></form></tr>|,thr(3),qq|<tr><td colspan="3" align="left"><b>$I{admregnew}</b></td></tr>|,
			frmadm('regnew'),qq|<tr><td align="right" colspan="2">$I{nickname}&nbsp;<input type="text" name="name" size="20" maxlength="$C{maxname}"></td><td>&nbsp;</td></tr><tr><td align="right" colspan="2">$I{password}&nbsp;<input type="text" name="pass" size="20"></td><td align="right"><input type="submit" value="$I{butadmregnew}"></td></form></tr>|,thr(3);
		}
	print qq|</table>$H{backtochat}</center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_sessions{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	print qq|</head>$H{begin_body}<center>|;
	print_sessions();
	print qq|<br>$H{backtochat}</center>$H{end_body}$H{end_html}|;
	exit;
}

sub print_sessions{
	sysopen(SESSIONS,"$datadir/sessions",O_RDONLY) or return;
	flock(SESSIONS,LOCK_SH) or return;
	my @lines=parse_sessions(<SESSIONS>);
	close SESSIONS;
	print qq|<h1>$I{admsessions}</h1><table border="0" cellpadding="5">|;
	print qq|<thead align="left"><tr><th><b>$I{nickname}</b></th><th><b>$I{timeoutin}</b></th><th><b>$I{ip}</b></th><th><b>$I{useragent}</b></th></tr></thead><tbody align="left" valign="middle">|;
	foreach(@lines){
		my %temp=sessionhash($_);
		print qq|<tr>|;
		my $s=$temp{status}==2?'':'&nbsp;';
		$s.=$I{symdenied}if$temp{status}==0;
		$s.=$I{symguest} if$temp{status}==1;
		$s.=$I{symmod}   if$temp{status}==6;
		$s.=$I{symadmin} if$temp{status}>=7;
		print qq|<td>|,style_this($temp{nickname}.$s,$temp{fontinfo}),qq|</td>|;
		print qq|<td align="center">|.get_timeout($temp{lastpost},$temp{status}).qq|</td>|;
		if($U{status}>$temp{status}or$U{session}eq$temp{session}){print qq|<td align="center">$temp{ip}</td><td>$temp{useragent}</td>|}
		else{print qq|<td align="center">-</td><td>-</td>|};
		print qq|</tr>|;
	}
	print qq|</tbody></table>|;
}

sub send_suspended{
	print qq|Refresh: 0; URL=$C{redirtourl}\n| if $C{redirifsusp};
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print qq|\n<meta http-equiv="Refresh" content="0; URL=$C{redirtourl}">| if $C{redirifsusp};
	print_stylesheet('error');
	print qq|</head>$H{begin_body}<h1>$I{suspended}</h1><p>|;
	print $I{susptext} unless $C{redirifsusp};
	print qq|<a href="$C{redirtourl}">$I{redirtext}</a>| if $C{redirifsusp};
	print qq|</p><hr>$H{end_body}$H{end_html}|;
	exit;
}

sub send_frameset{
	print qq|$H{begin_frames}<head>$H{meta_html}|;
	print_stylesheet();
	print qq|</head>\n<frameset rows="90,*,60" $C{frameattributes}><frame name="post" src="$S?action=post&session=$U{session}"><frame name="view" src="$S?action=entry&session=$U{session}"><frame name="controls" src="$S?action=controls&session=$U{session}"></frameset>$H{begin_body}$I{frames}$H{backtologin}$H{end_body}$H{end_html}|;
	exit;
}

sub send_messages{
	print qq|Refresh: $U{refresh}; URL=$S?action=view&session=$U{session}\n|;
	print qq|$H{begin_html}<head>$H{meta_html}\n<meta http-equiv="Refresh" content="$U{refresh}; URL=$S?action=view&session=$U{session}">|;
	print_stylesheet('view');
	print qq|</head>$H{begin_body}|;
	print_chatters();
	print_messages();
	print qq|$H{end_body}$H{end_html}|;
	exit;
}

sub send_choose_messages{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('view');
	print qq|</head>$H{begin_body}|,frmadm('clean');
	print qq|<input type="hidden" name="what" value="selected">|;
	print qq|<input type="submit" value="$I{butdelsome}" style="$C{styledelsome}"><br><br>|;
	print_select_messages();
	print qq|</form>$H{backtochat}$H{end_body}$H{end_html}|;
	exit;
}

sub send_post{
	$U{displayname}=$U{nickname};
	$U{displayname}=~s/\s+/&nbsp;/g;
	$U{displayname}=style_this($U{displayname},$U{fontinfo});
	$U{style}=get_style($U{fontinfo});
	$U{postid}=substr($^T,-6);
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('post');
	print qq|</head>$H{begin_body}<center><table border="0"><tr><td valign="top">$U{displayname}&nbsp;:</td>|,frmpst('post'),qq|<input type="hidden" name="postid" value="$U{postid}">|;
	print qq|<input type="hidden" name="multi" value="$Q{multi}[0]">| if $C{allowmultiline};
	if($Q{multi}[0] and $C{allowmultiline}){print qq|<td valign="top"><textarea name="message" wrap="virtual" rows="$U{boxheight}" cols="$U{boxwidth}" class="text" style="background-color:#$C{colbg};$U{style}">$U{rejected}</textarea></td>|}
	else{print qq|<td><input type="text" name="message" value="$U{rejected}" size="$U{boxwidth}" maxlength="$C{maxmessage}" class="text" style="background-color:#$C{colbg};$U{style}"></td>|}
	print qq|<td valign="top"><input type="submit" value="$I{butsendto}" class="send"></td><td valign="top"><select name="sendto" size="1" class="send" style="background-color:#$C{colbg};color:#$C{coltxt}">|;
	print '<option ';print 'selected ' if $Q{sendto}[0]eq'*';print 'value="*">-',$I{seltoall},'-</option>';
	if($U{status}>=2){print '<option ';print 'selected ' if $Q{sendto}[0]eq'?';print 'value="?">-',$I{seltomem},'-</option>'}
	if($U{status}>=6){print '<option ';print 'selected ' if $Q{sendto}[0]eq'#';print 'value="#">-',$I{seltoadmin},'-</option>'}
	if($C{allowpms}){
		foreach(sort {lc($a) cmp lc($b)} keys %X){
			unless($U{nickname}eq$_){
				print '<option ';print 'selected ' if $Q{sendto}[0]eq$X{$_}[0];
				print qq|value="$X{$_}[0]" style="$X{$_}[2]">$_</option>|;
			}
		}
	}
	print qq|</select></td></form></tr><tr><td colspan="4" height="6"></td></tr></table><table border="0"><tr>|,frmpst('delete','last'),qq|<td><input type="submit" value="$I{butdellast}" class="dellast"></td></form>|,frmpst('delete','all'),qq|<td><input type="submit" value="$I{butdelall}" class="delall"></td></form>|;
	if($C{allowmultiline}){
		print frmpst('post'),qq|<input type="hidden" name="sendto" value="$Q{sendto}[0]">|;
		if($Q{multi}[0]){print qq|<input type="hidden" name="multi" value=""><td width="10"></td><td><input type="submit" value="$I{butsingleline}" class="switch">|}
		else{print qq|<input type="hidden" name="multi" value="on"><td width="10"></td><td><input type="submit" value="$I{butmultiline}" class="switch">|}
		print qq|</td></form>|;
		
	}
	print qq|</tr></table></center>$H{end_body}$H{end_html}|;
	exit;
}

sub frmpst{my $f=qq|<form action="$S" method="post" target="post"><input type="hidden" name="action" value="$_[0]"><input type="hidden" name="session" value="$U{session}">|;$f.=qq|<input type="hidden" name="what" value="$_[1]"><input type="hidden" name="sendto" value="$Q{sendto}[0]"><input type="hidden" name="multi" value="$Q{multi}[0]">|if$_[1];return $f}

sub send_help{
	unless($C{rulestxt}=~/</){$C{rulestxt}=~s/\r\n/<br>/g;$C{rulestxt}=~s/\n/<br>/g;$C{rulestxt}=~s/\r/<br>/g}
	$C{rulestxt}=~s/<IP>/$ENV{'REMOTE_ADDR'}/g;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('profile');
	print qq|</head>$H{begin_body}<h2>$I{rules}</h2>$C{rulestxt}<br><hr><h2>$I{help}</h2>|;
	print qq|$I{helpguests}<br>| if $U{status}>=1;
	print qq|$I{helpregs}<br>|   if $U{status}>=2;
	print qq|$I{helpmods}<br>|   if $U{status}>=6;
	print qq|$I{helpadmins}<br>| if $U{status}>=7;
	print qq|<hr><center>$H{backtochat}<br><small>LE&nbsp;CHAT&nbsp;-&nbsp;$version</small></center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_profile{
	($U{colour})=$U{fontinfo}=~/#([0-9A-Fa-f]{6})/;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('profile');
	print qq|</head>$H{begin_body}<center><h2>$I{profileheader}</h2><i>$_[0]</i><table border="0">|,thr(3),qq|<form action="$S" method="post" target="view"><input type="hidden" name="action" value="profile"><input type="hidden" name="do" value="save"><input type="hidden" name="session" value="$U{session}"><tr><td align="left" colspan="2"><b>$I{refreshrate}</b> ($C{minrefresh}-$C{maxrefresh} $I{seconds})</td><td align="right"><input type="text" name="refresh" size="3" maxlength="3" value="$U{refresh}"></td></tr>|,thr(3),
		qq|<td align="left" colspan="2"><b>$I{fontcolour}</b> (<a href="$S?action=colours&session=$U{session}" target="view">$I{viewcolours}</a>)</td><td align="right"><input type="text" size="7" maxlength="6" value="$U{colour}" name="colour"></td></tr>|,thr(3);
	if($U{status}>=2 and $C{allowfonts}){
		print qq|<tr><td align="left"><b>$I{fontface}</b></td><td align="right">&nbsp;<select name="font" size="1"><option value="">$I{selchoose}</option>|;
		foreach(sort keys %F){
			print '<option style="',get_style($F{$_}),'" '; 
			print 'selected ' if $U{fontinfo}=~/$F{$_}/;
			print 'value="',$_,'">',$_,'</option>'
		}
		print qq|</select></td><td align="right">&nbsp;&nbsp;<input type="checkbox" name="bold" id="bold" value="on"|;print ' checked' if $U{fontinfo}=~/<i?bi?>/;
		print qq|><label for="bold">&nbsp;<b>$I{fontbold}</b></label>&nbsp;&nbsp;<input type="checkbox" name="italic" id="italic" value="on"|;print ' checked' if $U{fontinfo}=~/<b?ib?>/;
		print qq|><label for="italic">&nbsp;<i>$I{fontitalic}</i></label></td></tr>|,thr(3),qq||;
	}
	print qq|<tr><td colspan="3" align="center">|,style_this($I{fontexample},$U{fontinfo}),qq|</td></tr>|,thr(3),qq|<td align="left" colspan="2"><b>$I{boxsizes}</b></td><td align="right">$I{boxwidth}&nbsp;<input type="text" name="boxwidth" size="3" maxlength="3" value="$U{boxwidth}">|;
	print qq| &nbsp; $I{boxheight}&nbsp;<input type="text" name="boxheight" size="3" maxlength="3" value="$U{boxheight}">| if $C{allowmultiline};
	print qq|</td></tr>|,thr(3),qq||;
	if($U{status}>=2){
		print qq|<tr><td align="left" colspan="2"><b>$I{entryrefresh}</b> (1-$C{defaultrefresh} $I{seconds})</td><td align="right"><input type="text" name="entryrefresh" size="3" maxlength="3" value="$U{entryrefresh}"></td></tr>|,thr(3),
			qq|<tr><td align="left" colspan="3"><b>$I{changepass}</b></td></tr><tr><td align="right" colspan="3">$I{oldpass}&nbsp;<input type="password" name="oldpass" size="20"></td></tr><tr><td align="right" colspan="3">$I{newpass}&nbsp;<input type="password" name="newpass" size="20"></td></tr><tr><td align="right" colspan="3">$I{confirmpass}&nbsp;<input type="password" name="confirmpass" size="20"></td></tr>|,thr(3);
	}
	print qq|<tr><td align="center" colspan=3><input type="submit" value="$I{savechanges}"></td></tr></form></table><br>$H{backtochat}</center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_controls{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('controls');
	print qq|</head>$H{begin_body}<center><table border=0><tr><form action="$S" method="post" target="post"><input type="hidden" name="action" value="post"><input type="hidden" name="session" value="$U{session}"><td><input type="submit" value="$I{butreloadp}" class="reloadp"></td></form>|;
	print qq|<form action="$S" method="post" target="view"><input type="hidden" name="action" value="view"><input type="hidden" name="session" value="$U{session}"><td><input type="submit" value="$I{butreloadm}" class="reloadm"></td></form>|;
	print qq|<form action="$S" method="post" target="view"><input type="hidden" name="action" value="profile"><input type="hidden" name="session" value="$U{session}"><td><input type="submit" value="$I{butprofile}" class="profile"></td></form>|;
	print qq|<form action="$S" method="post" target="view"><input type="hidden" name="action" value="admin"><input type="hidden" name="session" value="$U{session}"><td><input type="submit" value="$I{butadmin}" class="admin"></td></form>| if $U{status}>=6;
	print qq|<form action="$S" method="post" target="view"><input type="hidden" name="action" value="help"><input type="hidden" name="session" value="$U{session}"><td><input type="submit" value="$I{butrules}" class="rules"></td></form>|;
	print qq|<form action="$S" method="post" target="_parent"><input type="hidden" name="action" value="logout"><input type="hidden" name="session" value="$U{session}"><td><input type="submit" value="$I{butexit}" class="exit"></td></form>|;
	print qq|</tr></table></center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_entry{
	$C{entrymessage}=~s/<NICK>/style_this($U{nickname},$U{fontinfo})/e;
	$I{entryhelp}=~s/<REFRESH>/$U{entryrefresh}/;
	print qq|Refresh: $U{entryrefresh}; URL=$S?action=view&session=$U{session}\n|;
	print qq|$H{begin_html}<head>$H{meta_html}\n<meta http-equiv="Refresh" content="$U{entryrefresh}; URL=$S?action=view&session=$U{session}">|;
	print_stylesheet('view');
	print qq|</head>$H{begin_body}<center><h1>$C{entrymessage}</h1></center><hr><small>$I{entryhelp}</small>$H{end_body}$H{end_html}|;
	exit;
}

sub send_logout{
	$C{logoutmessage}=~s/<NICK>/style_this($U{nickname},$U{fontinfo})/e;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('view');
	print qq|</head>$H{begin_body}<center><h1>$C{logoutmessage}</h1>$H{backtologin}</center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_colours{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('view');
	print qq|</head>$H{begin_body}<center><h2>$I{colheader}</h2><tt>|;
	for(my $red=0x00;$red<=0xFF;$red+=0x33){ 
		for(my $green=0x00;$green<=0xFF;$green+=0x33){ 
			for(my $blue=0x00;$blue<=0xFF;$blue+=0x33){
				my $hcol=sprintf('%02X',$red).sprintf('%02X',$green).sprintf('%02X',$blue);
				print "<font color=#$hcol","><b>$hcol</b></font> ";
			}print '<br>';
		}print '<br>';
	}
	print qq|</tt>$H{backtoprofile}</center>$H{end_body}$H{end_html}|;
	exit
}

sub send_login{
	my $nowchatting=get_nowchatting();
	$C{header}=~s/<IP>/$ENV{'REMOTE_ADDR'}/g;
	$C{footer}=~s/<IP>/$ENV{'REMOTE_ADDR'}/g;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('login');
	print qq|</head>$H{begin_body}<center>$C{header}<table $C{tableattributes}><form action="$S" method="post" target="_parent"><input type="hidden" name="action" value="login"><tr><td>$I{nickname}</td><td><input type="text" name="nick" size="15" class="text" maxlength="$C{maxname}"></td></tr><tr><td>$I{password}</td><td><input type="password" name="pass" size="15" class="text"></td></tr>|;
	if(($guests==1) or ($guests>=1 and $admincount>=1)){
		print qq|<tr><td colspan="2" align="center">$I{selcolguests}<br><select style="color:#$C{coltxt};background-color:#$C{colbg};" name="colour" class="view"><option value="">* |;
		print $C{rndguestcol}?$I{selcolrandom}:$I{selcoldefault},' *</option>';
		print_colours();
		print qq|</select></td></tr>|;
	}
	elsif($C{noguests}){
		print qq|<tr><td colspan="2" align="center">$C{noguests}</td></tr>|;
	}
	print qq|<tr><td colspan="2" align="center"><input type="submit" value="$C{loginbutton}" class="enter"></td></tr>\n</table></form>$nowchatting|;
	print qq|$C{footer}</center>$H{end_body}$H{end_html}|;
	exit;
}

sub send_error{my($err,$nick)=@_;
	$nick=style_this($U{nickname},$U{fontinfo}) unless "$nick";
	$nick=style_this($nick,$X{$nick}[2]) if $X{$nick}[2];
	$err=~s/<NICK>/$nick/;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('error');
	print qq|</head>$H{begin_body}<h2>$I{error}$err</h2>$H{backtologin}$H{end_body}$H{end_html}|;
	exit;
}

sub send_warning{my($err,$nick)=@_;
	$nick=style_this($U{nickname},$U{fontinfo}) unless "$nick";
	$nick=style_this($nick,$X{$nick}[2]) if $X{$nick}[2];
	$err=~s/<NICK>/$nick/;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('error');
	print qq|</head>$H{begin_body}<h2>$I{error} $err</h2>$H{backtochat}$H{end_body}$H{end_html}|;
	exit;
}

sub send_fatal{
	return if $Q{action}[0]=~/^setup|init$/;
	set_html_vars();
	print qq|Content-Type: text/html; charset=$I{charset}\nPragma: no-cache\nExpires: 0\n|;
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('error');
	print qq|</head>$H{begin_body}<h2>Fatal Error!</h2>$_[0]$H{end_body}$H{end_html}|;
	exit;
}

sub print_chatters{
	print qq|<table border="0"><tr>|;
	print_waiting() if($guests==3 and $U{status}>=7);
	print qq|<td valign="top"><u>$I{members}</u>&nbsp;</td><td valign="top">|,join(' &nbsp; ',@M),'</td><td>&nbsp;</td>' if @M;
	print qq|<td valign="top"><u>$I{guests}</u>&nbsp;</td><td valign="top">|,join(' &nbsp; ',@G),'</td><td>&nbsp;</td>' if @G;
	print qq|</tr></table><br>|;
}

sub print_waiting{
	my $count=get_waiting_count();
	return unless $count;
	$I{butcheckwait}=~s/<COUNT>/$count/;
	print qq|<form action="$S" method="post"><input type="hidden" name="action" value="admin"><input type="hidden" name="do" value="newcomers"><input type="hidden" name="session" value="$U{session}"><td valign="top" align="right"><input type="submit" value="$I{butcheckwait}" style="$C{stylecheckwait}"></td><td>&nbsp;</td></form>|;
}

sub print_memberslist{
	read_members();
	foreach(sort {lc($a) cmp lc($b)} keys %A){
		if(!$_[0] or $A{$_}[1]==$_[0]){
			print qq|<option value="$A{$_}[0]" style="$A{$_}[2]">$_|;
			unless($_[0]){
				print ' ',$I{symdenied} if $A{$_}[1]==0;   
				print ' ',$I{symmod} if $A{$_}[1]==6;
				print ' ',$I{symadmin} if $A{$_}[1]>=7;
			}
			print '</option>';
		}
	}
}

sub print_stylesheet{
	print qq|\n<style type="text/css"><!--\n$C{cssglobal}\n|;
	if($_[0]eq'view'){
		print $C{cssview},"input.back{$C{styleback}}\n";
	}
	elsif($_[0]eq'post'){
		print $C{csspost};
		print "input.text{$C{styleposttext}}\n";
		print "textarea.text{$C{styleposttext}}\n";
		print "input.send{$C{stylepostsend}}\n";
		print "select.send{$C{stylesendlist}}\n";
		print "input.dellast{$C{styledellast}}\n";
		print "input.delall{$C{styledelall}}\n";
		print "input.switch{$C{styleswitch}}\n" if $C{allowmultiline};
	}
	elsif($_[0]eq'controls'){
		print $C{csscontrols};
		print "input.reloadp{$C{stylerelpost}}\n";
		print "input.reloadm{$C{stylerelmes}}\n";  
		print "input.profile{$C{styleprofile}}\n";
		print "input.admin{$C{styleadmin}}\n" if $U{status}>=6;
		print "input.rules{$C{stylerules}}\n";
		print "input.exit{$C{styleexit}}\n";
	}
	elsif($_[0]eq'login'){
		print $C{csslogin};
		print "input.text{$C{stylelogintext}}\n";  
		print "select.view{$C{stylecolselect}}\n";  
		print "input.enter{$C{styleenter}}\n";  
	}
	elsif($_[0]eq'wait'){
		print $C{csswait},"\n"; 
	}
	elsif($_[0]eq'error'){
		print $C{csserror},"input.back{$C{styleback}}\n"; 
	}
	elsif($_[0]eq'profile'){
		print $C{cssprofile},"input.back{$C{styleback}}\n"; 
	}
	elsif($_[0]eq'admin'){
		print $C{cssadmin},"input.back{$C{styleback}}\n"; 
	}
	print qq|$H{add_css}--></style>\n|;
}

######################################################################
# session management
######################################################################

sub create_session{
	send_error($I{errbadnick}) unless valid_nick($Q{nick}[0]);
	$U{nickname}=$Q{nick}[0];
	$U{nickname}=~s/^\s+//;
	$U{nickname}=~s/\s+$//;
	$U{nickname}=~s/\s+/ /g;
	$U{passhash}=hash_this($U{nickname}.$Q{pass}[0]);
	$U{colour}=$Q{colour}[0];
	$U{status}=1;
	check_member();
	send_error($I{erraccdenied}) if $U{status}==0 or $U{status}>8;
	add_user_defaults();
	if($U{status}==1){#we have a guest:
		send_error($I{errnoguests}) unless $guests; 
		send_error($I{errbadpass}) unless valid_pass($Q{pass}[0]);
		create_waiting_session() if $guests==3;# send guest to waiting room
	}
	# read and update current sessions
	sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
	my @lines=parse_sessions(<SESSIONS>);
	my %sids;my $reentry=0;my $inuse=0;my $kicked=0;
	for(my $i=$#lines; $i>=0;$i--){
		my %temp=sessionhash($lines[$i]);
		$sids{$temp{session}}=1;# collect all existing ids
		if(similar_nick($temp{nickname},$U{nickname})){# nick already here?
			$kicked=1  if $temp{status}==0;
			$reentry=1 if($U{status}>=2 or $U{passhash}eq$temp{passhash});
			$inuse=1   if($U{status}<2 and $U{passhash}ne$temp{passhash});
			unless($kicked){splice(@lines,$i,1) if $reentry}
		}
	}
	# create new session:
	unless($inuse or $kicked){
		unless($U{status}==1 and $guests>=2 and $admincount==0){
			do{$U{session}=hash_this(time.rand().$U{nickname})}while($sids{$U{session}});# check for hash collision
			push(@lines,sessionline(%U));
		}
	}
	seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
	truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
	print SESSIONS @lines;
	close SESSIONS or send_error("$I{errfile} (sessions/close)");
	send_error($I{errbadlogin}) if $inuse;
	send_error($C{kickederror}) if $kicked;
	send_error($I{errnoguests}) if($U{status}==1 and (!$guests or $guests>1 and !$admincount));
	clean_room() unless(keys %X);
	add_system_message($C{roomentry}) unless $reentry;
}

sub kick_chatter{
	send_admin() if $Q{name}[0]eq'';
	my $kickednick='';
	sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
	my @lines=parse_sessions(<SESSIONS>);
	foreach(@lines){
		my %temp=sessionhash($_);
		if(unpack('H*',$temp{nickname})eq$Q{name}[0] and $temp{status}!=0){
			$temp{status}='0';
			$temp{lastpost}=60*($C{kickpenalty}-$C{guestsexpire})+$^T;
			$_=sessionline(%temp);
			$kickednick=style_this($temp{nickname},$temp{fontinfo});
		}
	}
	push(@lines,sessionline(%U)) if $U{session};
	seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
	truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
	print SESSIONS @lines;
	close SESSIONS or send_error("$I{errfile} (sessions/close)");
	add_system_message($C{kickedmessage},$kickednick) if $kickednick;
	return if $kickednick;
	$I{errcantkick}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
	send_admin($I{errcantkick}); 
}

sub update_sessions{
	sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
	my @lines=parse_sessions(<SESSIONS>);
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
	push @lines,sessionline(%U) if $U{session};
	seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
	truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
	print SESSIONS @lines;
	close(SESSIONS) or send_error("$I{errfile} (sessions/close)");
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror}) if $U{status}==0;
	send_error($I{errnoguests}) if($U{status}==1 and (!$guests or $guests>1 and !$admincount));
}

sub check_session{
	sysopen(SESSIONS,"$datadir/sessions",O_RDONLY) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_SH) or send_error("$I{errfile} (sessions/lock)");
	parse_sessions(<SESSIONS>);
	close(SESSIONS);
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror}) if $U{status}==0;
	send_error($I{errnoguests}) if($U{status}==1 and (!$guests or $guests>1 and !$admincount));
}

sub kill_session{
	sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
	my @lines=parse_sessions(<SESSIONS>);
	seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
	truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
	print SESSIONS @lines;
	close(SESSIONS) or send_error("$I{errfile} (sessions/close)");
	send_error($I{errexpired}) unless $U{session};
	send_error($C{kickederror}) if($U{status}==0);
	if(scalar keys %X>1){# still chatters in room
		add_system_message($C{roomexit});  
	}else{clean_room()}
}

sub get_nowchatting{
	sysopen(SESSIONS,"$datadir/sessions",O_RDONLY) or return;
	flock(SESSIONS,LOCK_SH) or return;
	parse_sessions(<SESSIONS>);
	close SESSIONS;	
	$C{nowchatting}=~s/<NAMES>/join(' &nbsp; ',(@M,@G))/e;
	$C{nowchatting}=~s/<COUNT>/@M+@G/e;
	return "$C{nowchatting}<br>";
}

sub parse_sessions{my @lines=@_;
# returns cleaned up sessions minus that of the current user and populates global variables
	my %temp;my $i;%X=();@G=();@M=();$admincount=0;
	# we need admincount first
	for($i=$#lines; $i>=0;$i--){
		%temp=sessionhash($lines[$i]);
		if(expireds($temp{lastpost},$temp{status})){
			splice(@lines,$i,1);
		}elsif($temp{status}>=7){
			$admincount++;
		}
	}
	# fill variables, clean up guests if needed
	for($i=$#lines; $i>=0;$i--){
		%temp=sessionhash($lines[$i]);
		if($temp{session}eq$Q{session}[0]){
			%U=%temp;
			add_user_defaults();
			splice(@lines,$i,1) unless $Q{action}[0]eq'admin' and $Q{do}[0]eq'sessions' or $temp{status}==0;
		}
		if($temp{status}>=2){
			$X{$temp{nickname}}=[unpack('H*',$temp{nickname}),$temp{status},get_style($temp{fontinfo})];
			$temp{nickname}=~s/\s+/&nbsp;/g;
			push(@M,style_this($temp{nickname},$temp{fontinfo}));
		}elsif($temp{status}==1){
			if(!$guests or $guests>1 and !$admincount){
				splice(@lines,$i,1) unless($temp{session}eq$Q{session}[0]);
			}else{
				$X{$temp{nickname}}=[unpack('H*',$temp{nickname}),$temp{status},get_style($temp{fontinfo})];
				$temp{nickname}=~s/\s+/&nbsp;/g;
				push(@G,style_this($temp{nickname},$temp{fontinfo}));
			}
		}
	}
	return @lines;
}

sub sessionhash{
	my @fields=split('l',$_[0]);  
	my %s=(
		session      =>          $fields[ 0] ,
		nickname     =>pack('H*',$fields[ 1]),
		status       =>pack('H*',$fields[ 2]),
		refresh      =>pack('H*',$fields[ 3]),
		fontinfo     =>pack('H*',$fields[ 4]),
		lastpost     =>pack('H*',$fields[ 5]),
		passhash     =>          $fields[ 6] ,
		postid       =>pack('H*',$fields[ 7]),
		entryrefresh =>pack('H*',$fields[ 8]),
		boxwidth     =>pack('H*',$fields[ 9]),
		boxheight    =>pack('H*',$fields[10]),
		ip           =>pack('H*',$fields[11]),
		useragent    =>pack('H*',$fields[12]),
	);
	return %s;
}

sub sessionline{
	my %s=@_;
	my $session= 
		            $s{session}      .'l'.
		unpack('H*',$s{nickname})    .'l'.
		unpack('H*',$s{status})      .'l'.
		unpack('H*',$s{refresh})     .'l'.
		unpack('H*',$s{fontinfo})    .'l'.
		unpack('H*',$s{lastpost})    .'l'.
		            $s{passhash}     .'l'.
		unpack('H*',$s{postid})      .'l'.
		unpack('H*',$s{entryrefresh}).'l'.
		unpack('H*',$s{boxwidth})    .'l'.
		unpack('H*',$s{boxheight})   .'l'.
		unpack('H*',$s{ip})          .'l'.
		unpack('H*',$s{useragent})   .'l'.
		"\n";
	return $session;
}

######################################################################
# waiting room handling
######################################################################

sub create_waiting_session{
	# check if name used in room already
	sysopen(SESSIONS,"$datadir/sessions",O_RDONLY) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_SH) or send_error("$I{errfile} (sessions/lock)");
	my @lines=parse_sessions(<SESSIONS>);
	close(SESSIONS);
	foreach(@lines){
		my %temp=sessionhash($_);
		if(similar_nick($temp{nickname},$U{nickname})){
			if($temp{passhash}eq$U{passhash}){# reentry, approved already
				%U=%temp;
				send_error($C{kickederror}) if $U{status}==0;
				send_frameset();
			}
			else{send_error($I{errbadlogin})}# name in use
		}
	}
	# remove expired waiting entries
	sysopen(WAITING,"$datadir/waiting",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (waiting/open)");
	flock(WAITING,LOCK_EX) or send_error("$I{errfile} (waiting/lock)");
	my @lines=parse_waitings(<WAITING>);
	my %sids;my $reentry;my $inuse;
	foreach(@lines){
		my %temp=waitinghash($_);
		$sids{$temp{session}}=1;# collect all existing ids
		if(similar_nick($temp{nickname},$U{nickname})){# nick already waiting?
			if($U{passhash}eq$temp{passhash}){
				$reentry=1;
				%U=%temp;
				$U{status}=1;# needs reapproval since no session in room was made
			}else{
				$inuse=1;
			}
		}
	}
	# create new waiting session:
	unless($inuse or $reentry or !$admincount){
		$U{status}=1;
		add_user_defaults();
		do{$U{session}=hash_this(time.rand().$U{nickname})}while($sids{$U{session}});# check for hash collision
		push(@lines,waitingline(%U));
	}
	seek(WAITING,0,0) or send_error("$I{errfile} (waiting/seek)");
	truncate(WAITING,0) or send_error("$I{errfile} (waiting/truncate)");
	print WAITING @lines;
	close WAITING or send_error("$I{errfile} (waiting/close)");
	send_error($I{errbadlogin}) if $inuse;
	send_error($I{errnoguests}) if(!$guests or $guests>1 and !$admincount);
	send_waiting_room();
}

sub check_waiting_session{
	sysopen(WAITING,"$datadir/waiting",O_RDONLY) or send_error("$I{errfile} (waiting/open)");
	flock(WAITING,LOCK_SH) or send_error("$I{errfile} (waiting/lock)");
	parse_waitings(<WAITING>);
	close(WAITING);
	send_error($I{errexpired}) unless $U{session};
	send_error($I{erraccdenied}) if($U{status}==0);
	if($U{status}==2 or $guests==1){# approved or guest settings changed: create new session, send frameset
		sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
		flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
		my @lines=parse_sessions(<SESSIONS>);
		my %sids;my $reentry=0;my $inuse=0;my $kicked=0;
		for(my $i=$#lines; $i>=0;$i--){
			my %temp=sessionhash($lines[$i]);
			$sids{$temp{session}}=1;# collect all existing ids
			if(similar_nick($temp{nickname},$U{nickname})){# nick already here?
				$kicked=1  if $temp{status}==0;
				$reentry=1 if $U{passhash}eq$temp{passhash};
				$inuse=1   if $U{passhash}ne$temp{passhash};
				splice(@lines,$i,1) if $reentry;
			}
		}
		# create new session:
		unless($inuse or $kicked){
			unless(!$guests or $guests>1 and !$admincount){# in case guest settings just changed
				$U{status}=1;
				add_user_defaults();
				do{$U{session}=hash_this(time.rand().$U{nickname})}while($sids{$U{session}});# check for hash collision
				push(@lines,sessionline(%U));
			}
		}
		seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
		truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
		print SESSIONS @lines;
		close SESSIONS or send_error("$I{errfile} (sessions/close)");
		send_error($I{errbadlogin}) if $inuse;
		send_error($C{kickederror}) if $kicked;
		send_error($I{errnoguests}) if($U{status}==1 and (!$guests or $guests>1 and !$admincount));
		add_system_message($C{roomentry}) unless $reentry;
		send_frameset();
	}
}

sub send_waiting_room{
	$I{waitmessage}=~s/<REFRESH>/$C{defaultrefresh}/;
	$I{waitmessage}=~s/<NICK>/<font color=\"$U{colour}\">$U{nickname}<\/font>/;
	print qq|Refresh: $C{defaultrefresh}; URL=$S?action=wait&session=$U{session}\n|;
	print qq|$H{begin_html}<head>$H{meta_html}\n<meta http-equiv="Refresh" content="$C{defaultrefresh}; URL=$S?action=wait&session=$U{session}">\n|;
	print_stylesheet('wait');
	print qq|</head>$H{begin_body}<center><h2>$I{waitroom}</h2>$I{waitmessage}<br><br>|;
	print qq|<form action="$S" method="post"><input type="hidden" name="action" value="wait"><input type="hidden" name="session" value="$U{session}"><input type="submit" value="$I{butreloadw}" style="$C{stylewaitrel}"></form>|;
	print qq|</center>$H{end_body}$H{end_html}|;
exit;
}

sub send_waiting_admin{
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	print qq|</head>$H{begin_body}<center><h2>$I{admwaiting}</h2>|;
	sysopen(WAITING,"$datadir/waiting",O_RDONLY) or send_error("$I{errfile} (waiting/open)");
	flock(WAITING,LOCK_SH) or send_error("$I{errfile} (waiting/lock)");
	my @lines=parse_waitings(<WAITING>);
	close(WAITING);
	my $waitings=0;
	foreach(@lines){
		my %temp=waitinghash($_);
		$waitings++ if $temp{status}==1;
	}
	if($waitings){
		print qq|<form action="$S" method="post"><input type="hidden" name="action" value="admin"><input type="hidden" name="do" value="newcomers"><input type="hidden" name="session" value="$U{session}"><table border=0 cellpadding=5><thead align="left"><tr><th><b>$I{nickname}</b></th><th><b>$I{ip}</b></th><th><b>$I{useragent}</b></th></tr></thead><tbody align="left" valign="middle">|;
		foreach(@lines){
			my %temp=waitinghash($_);
			next if $temp{status}<=>1;
			print qq|<tr><input type="hidden" name="alls" value="$temp{session}"><td><input type="checkbox" name="csid" id="$temp{session}" value="$temp{session}"><label for="$temp{session}">&nbsp;<font color="#$temp{colour}">$temp{nickname}</font></label></td><td>$temp{ip}</td><td>$temp{useragent}</td></tr>|;
		}
		print qq|</tbody></table><table border="0"><tr><td><input type="radio" name="what" value="allowchecked" id="allowchecked" checked></td><td><label for="allowchecked"> $I{allowchecked}&nbsp;&nbsp;</label></td><td><input type="radio" name="what" value="allowall" id="allowall"></td><td><label for="allowall"> $I{allowall}&nbsp;&nbsp;</label></td><td><input type="radio" name="what" value="denychecked" id="denychecked"></td><td><label for="denychecked"> $I{denychecked}&nbsp;&nbsp;</label></td><td><input type="radio" name="what" value="denyall" id="denyall"></td><td><label for="denyall"> $I{denyall}&nbsp;&nbsp;</label></td><td><input type="submit" value="$I{butadmdo}"></td></tr></table></form><br>|;
	}else{
		print "$I{waitempty}<br><br>";
	}
	print qq|$H{backtochat}</center>$H{end_body}$H{end_html}|;
	exit;
}

sub get_waiting_count{
	# return number of sessions to be approved, for admin-button
	sysopen(WAITING,"$datadir/waiting",O_RDONLY) or send_error("$I{errfile} (waiting/open)");
	flock(WAITING,LOCK_SH) or send_error("$I{errfile} (waiting/lock)");
	my @lines=parse_waitings(<WAITING>);
	close(WAITING);
	my $waitings=0;
	foreach(@lines){
		my %temp=waitinghash($_);
		$waitings++ if $temp{status}==1;
	}
	return $waitings;
}

sub parse_waitings{my @lines=@_;
	# returns cleaned up sessions and populates global variable
	for(my $i=$#lines; $i>=0;$i--){
		my %temp=waitinghash($lines[$i]);
		if(expiredw($temp{timestamp})){
			splice(@lines,$i,1);
		}elsif($Q{session}[0]eq$temp{session}){
			%U=%temp;
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
	sysopen(WAITING,"$datadir/waiting",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (waiting/open)");
	flock(WAITING,LOCK_EX) or send_error("$I{errfile} (waiting/lock)");
	my @lines=parse_waitings(<WAITING>);
	foreach my $wait (@lines){
		my %temp=waitinghash($wait);
		if($temp{status}==1 and $sids{$temp{session}}){$temp{status}=$newstatus}
		$wait=waitingline(%temp);
	}
	seek(WAITING,0,0) or send_error("$I{errfile} (waiting/seek)");
	truncate(WAITING,0) or send_error("$I{errfile} (waiting/truncate)");
	print WAITING @lines;
	close WAITING or send_error("$I{errfile} (waiting/close)");
}

sub waitinghash{
	my @fields=split('l',$_[0]);  
	my %w=(
		session   =>          $fields[0],
		timestamp =>pack('H*',$fields[1]),
		nickname  =>pack('H*',$fields[2]),
		passhash  =>          $fields[3] ,
		colour    =>pack('H*',$fields[4]),
		ip        =>pack('H*',$fields[5]),
		useragent =>pack('H*',$fields[6]),
		status    =>pack('H*',$fields[7]),
	);
	return %w;
}

sub waitingline{
	my %w=@_;
	my $wline= 
		            $w{session}   .'l'.
		unpack('H*',$w{timestamp}).'l'.
		unpack('H*',$w{nickname}) .'l'.
		            $w{passhash}  .'l'.
		unpack('H*',$w{colour})   .'l'.
		unpack('H*',$w{ip})       .'l'.
		unpack('H*',$w{useragent}).'l'.
		unpack('H*',$w{status})   .'l'.
		"\n";
	return $wline;
}

######################################################################
# member handling
######################################################################

sub valid_admin{
	($U{nickname},$U{pass})=@_;
	# main admin?
	$U{passhash}=hash_this($U{nickname}.$U{pass});
	sysopen(MEMBERS,"$datadir/members",O_RDONLY) or send_error("$I{errfile} (members/open)");
	flock(MEMBERS,LOCK_SH) or send_error("$I{errfile} (members/lock)");
	while(<MEMBERS>){
		my %temp=memberhash($_);
		if($temp{nickname}eq$U{nickname}){
			if($temp{passhash}eq$U{passhash} and $temp{status}==8){
				close MEMBERS;
				return 1
			}
		}
	}
	close MEMBERS;
	# superuser?
	$U{passhash}=hash_this($U{nickname}.hash_this($U{nickname}).hash_this($U{pass}).$U{pass});
	sysopen(ADMIN,"$datadir/admin",O_RDONLY) or send_error("$I{errfile} (admin/open)");
	flock(ADMIN,LOCK_SH) or send_error("$I{errfile} (admin/lock)");
	my $sudata=<ADMIN>;
	close(ADMIN);
	if($U{passhash}eq$sudata){
		$U{status}=9;
		return 2
	}
	return 0
}

sub check_member{  
	sysopen(MEMBERS,"$datadir/members",O_RDONLY) or send_error("$I{errfile} (members/open)");
	flock(MEMBERS,LOCK_SH) or send_error("$I{errfile} (members/lock)");
	my $cnick=$U{nickname};$cnick=~s/[^a-z0-9]//ig;
	while(<MEMBERS>){
		my %temp=memberhash($_);
		if($temp{nickname}eq$U{nickname}){
			if($temp{passhash}eq$U{passhash}){
				%U=%temp;
				last;
			}else{send_error($I{errbadlogin})}
		}
		my $tnick=$temp{nickname};$tnick=~s/[^a-z0-9]//ig;
		send_error($I{errbadlogin}) if $cnick=~/^$tnick$/i;
	}
	close MEMBERS;
}

sub read_members{
	sysopen(MEMBERS,"$datadir/members",O_RDONLY) or return;
	flock(MEMBERS,LOCK_SH) or return;
	%A=(); 
	while(<MEMBERS>){
		my %temp=memberhash($_);
		$A{$temp{nickname}}=[unpack('H*',$temp{nickname}),$temp{status},get_style("#$temp{colour} $F{$temp{fontface}} <$temp{fonttags}>")];  
	}
	close MEMBERS;
}

sub register_guest{
	send_admin() if $Q{name}[0]eq'';
	unless($X{pack('H*',$Q{name}[0])}[1]==1){
		$I{errcantreg}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
		send_admin($I{errcantreg});
	}
	sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
	my @lines=<SESSIONS>;
	seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
	truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
	my %reg;
	foreach(@lines){
		my %temp=sessionhash($_); 
		if(unpack('H*',$temp{nickname})eq$Q{name}[0] and $temp{status}==1){
			%reg=%temp;
			$reg{status}=2;$temp{status}=2;
			($reg{colour})=$reg{fontinfo}=~/#([a-f0-9]{6})/i;
			print SESSIONS sessionline(%temp);
		}  
		else{
			print SESSIONS $_ unless expireds($temp{lastpost},$temp{status});
		}  
	}
	unless($reg{status}){
		close SESSIONS;
		$I{errcantreg}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
		send_admin($I{errcantreg});
	}
	sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (members/open)");
	flock(MEMBERS,LOCK_EX) or send_error("$I{errfile} (members/lock)");
	my @lines=<MEMBERS>;
	#backup_members(@lines);
	seek(MEMBERS,0,0) or send_error("$I{errfile} (members/seek)");
	truncate(MEMBERS,0) or send_error("$I{errfile} (members/truncate)");
	print MEMBERS @lines;
	foreach(@lines){
		my %temp=memberhash($_);
		if(unpack('H*',$temp{nickname})eq$Q{name}[0]){
			close MEMBERS;
			close SESSIONS;
			$I{erralreadyreg}=~s/<NICK>/pack('H*',$Q{name}[0])/e;
			send_admin($I{erralreadyreg});
		}
	}
	print MEMBERS memberline(%reg);
	close MEMBERS or send_error("$I{errfile} (members/close)");
	add_system_message($C{regmessage},style_this($reg{nickname},$reg{fontinfo}));
	close SESSIONS or send_error("$I{errfile} (sessions/close)");
}

sub register_new{
	send_admin() if $Q{name}[0]eq'';
	if($X{$Q{name}[0]}){
		$I{errcantregnew}=~s/<NICK>/$Q{name}[0]/;
		send_admin($I{errcantreg});
	}
	send_admin($I{errbadnick}) unless valid_nick($Q{name}[0]);
	send_admin($I{errbadpass}) unless valid_pass($Q{pass}[0]);
	sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (members/open)");
	flock(MEMBERS,LOCK_EX) or send_error("$I{errfile} (members/lock)");
	my @lines=<MEMBERS>;
	#backup_members(@lines);
	seek(MEMBERS,0,0) or send_error("$I{errfile} (members/seek)");
	truncate(MEMBERS,0) or send_error("$I{errfile} (members/truncate)");
	print MEMBERS @lines;
	foreach(@lines){
		my %temp=memberhash($_);
		if(unpack('H*',$temp{nickname})eq$Q{name}[0]){
			close MEMBERS;
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
	print MEMBERS memberline(%reg);
	close MEMBERS or send_error("$I{errfile} (members/close)");
	$I{succreg}=~s/<NICK>/$Q{name}[0]/;
	send_admin($I{succreg});
}

sub change_status{
	send_admin() if($Q{name}[0]eq'' or $Q{set}[0]eq'');
	my $nick=pack('H*',$Q{name}[0]);
	if($U{status}<=$Q{set}[0] or $Q{set}[0]!~/^[0267\-]$/){
		$I{errcantstatus}=~s/<NICK>/$nick/;
		send_admin($I{errcantstatus})
	}
	my $found=0;
	sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (members/open)");
	flock(MEMBERS,LOCK_EX) or send_error("$I{errfile} (members/lock)");
	my @lines=<MEMBERS>;
	#backup_members(@lines);
	seek(MEMBERS,0,0) or send_error("$I{errfile} (members/seek)");
	truncate(MEMBERS,0) or send_error("$I{errfile} (members/truncate)");
	foreach(@lines){
		my %temp=memberhash($_);
		if(unpack('H*',$temp{nickname})eq$Q{name}[0] and $U{status}>$temp{status}){
			$found=1;
			next if $Q{set}[0]eq'-';
			$found=2;
			$temp{status}=$Q{set}[0];
			print MEMBERS memberline(%temp);
		}
		else{
			print MEMBERS $_;
		}
	}
	close MEMBERS or send_error("$I{errfile} (members/close)");
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

sub save_profile{
	send_profile($I{errdiffpass}) if $Q{newpass}[0]ne$Q{confirmpass}[0];
	# check data
	$U{refresh}=$Q{refresh}[0];
	$U{refresh}=$C{minrefresh} if $U{refresh}<$C{minrefresh};
	$U{refresh}=$C{maxrefresh} if $U{refresh}>$C{maxrefresh};
	$U{colour}=$Q{colour}[0]; unless($U{colour}=~/^[a-f0-9]{6}$/i){$U{colour}=$C{coltxt}}
	$U{fonttags}='';
	$U{fonttags}.='b' if($Q{bold}[0] and $U{status}>=2);
	$U{fonttags}.='i' if($Q{italic}[0] and $U{status}>=2);
	$U{fontface}=$Q{font}[0] if($F{$Q{font}[0]} and $U{status}>=2);
	$U{fontinfo}="#$U{colour} $F{$U{fontface}} <$U{fonttags}>";  
	$U{entryrefresh}=$Q{entryrefresh}[0];
	$U{entryrefresh}=1 if $U{entryrefresh}<1;
	$U{entryrefresh}=$C{defaultrefresh} if $U{entryrefresh}>$C{defaultrefresh};
	$U{boxwidth}=$Q{boxwidth}[0] if $Q{boxwidth}[0]>0;
	$U{boxheight}=$Q{boxheight}[0] if $Q{boxheight}[0]>0;
	$U{boxwidth}=$C{boxwidthdef} unless($U{boxwidth}<1000);
	$U{boxheight}=$C{boxheightdef} unless($U{boxheight}<1000);
	# rewrite session
	sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (sessions/open)");
	flock(SESSIONS,LOCK_EX) or send_error("$I{errfile} (sessions/lock)");
	my @lines=<SESSIONS>;
	seek(SESSIONS,0,0) or send_error("$I{errfile} (sessions/seek)");
	truncate(SESSIONS,0) or send_error("$I{errfile} (sessions/truncate)");
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{session}eq$U{session}){
			print SESSIONS sessionline(%U);
		}
		else{
			print SESSIONS $_ unless expireds($temp{lastpost},$temp{status});
		}
	}
	close SESSIONS or send_error("$I{errfile} (sessions/close)");
	if($U{status}>=2){# rewrite member file
		my $err='';
		sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (members/open)");
		flock(MEMBERS,LOCK_EX) or send_error("$I{errfile} (members/lock)");
		my @lines=<MEMBERS>;
		#backup_members(@lines);
		seek(MEMBERS,0,0) or send_error("$I{errfile} (members/seek)");
		truncate(MEMBERS,0) or send_error("$I{errfile} (members/truncate)");
		foreach(@lines){
			my %temp=memberhash($_);
			if($temp{nickname}eq$U{nickname}){  
				if($Q{oldpass}[0]){
					$err=$I{errbadpass} unless valid_pass($Q{newpass}[0]);
					$err=$I{errwrongpass} unless $temp{passhash} eq hash_this($U{nickname}.$Q{oldpass}[0]);
					$U{passhash}=hash_this($U{nickname}.$Q{newpass}[0]) unless $err;
				}
				if($err){print MEMBERS $_}else{print MEMBERS memberline(%U)}
			}
			else{
				print MEMBERS $_;
			}
		}
		close MEMBERS or send_error("$I{errfile} (members/close)");
		send_profile($err) if $err;
	}
	send_profile($I{succchanged});
}

sub memberhash{
	my @fields=split('l',$_[0]);
	my %m=(
		nickname     =>pack('H*',$fields[0]),
		passhash     =>          $fields[1] , 
		status       =>pack('H*',$fields[2]),
		refresh      =>pack('H*',$fields[3]),
		colour       =>pack('H*',$fields[4]),
		fontface     =>pack('H*',$fields[5]),
		fonttags     =>pack('H*',$fields[6]),
		entryrefresh =>pack('H*',$fields[7]),
		boxwidth     =>pack('H*',$fields[8]),
		boxheight    =>pack('H*',$fields[9]),
	);
	return %m;
}

sub memberline{
	my %m=@_;
	my $member=
		unpack('H*',$m{nickname})    .'l'.
		            $m{passhash}     .'l'.
		unpack('H*',$m{status})      .'l'.
		unpack('H*',$m{refresh})     .'l'.
		unpack('H*',$m{colour})      .'l'.
		unpack('H*',$m{fontface})    .'l'.
		unpack('H*',$m{fonttags})    .'l'.
		unpack('H*',$m{entryrefresh}).'l'.
		unpack('H*',$m{boxwidth})    .'l'.
		unpack('H*',$m{boxheight})   .'l'.
		"\n";
	return $member;
}

sub add_user_defaults{
	$U{ip}=$ENV{'REMOTE_ADDR'};
	$U{useragent}=$ENV{'HTTP_USER_AGENT'};
	$U{useragent}=~s/&/&amp;/g;
	$U{useragent}=~s/</&lt;/g;
	$U{useragent}=~s/>/&gt;/g;
	$U{useragent}=~s/"/&quot;/g;
	$U{refresh}=$C{defaultrefresh} unless $U{refresh};
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
	$U{entryrefresh}=$C{defaultrefresh} unless $U{entryrefresh}>0;
	$U{boxwidth}=$C{boxwidthdef} unless $U{boxwidth};
	$U{boxheight}=$C{boxheightdef} unless $U{boxheight};
	$U{timestamp}=$^T unless $U{timestamp};
	$U{lastpost}=$^T unless $U{lastpost};
	$U{postid}='OOOOOO' unless $U{postid};
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
		$U{rejected}=~s/</&lt;/g;
		$U{rejected}=~s/>/&gt;/g;
		$U{rejected}=~s/"/&quot;/g;
		$U{rejected}=~s/\r\n/<br>/g;
		$U{rejected}=~s/\n/<br>/g;
		$U{rejected}=~s/\r/<br>/g;
		$U{rejected}=~s/<br>(<br>)+/<br><br>/g;
		$U{rejected}=~s/<br><br>$/<br>/;
		$U{rejected}=~s/<br>/\n/g if $C{allowmultiline};
		$U{rejected}=~s/<br>/ /g unless $C{allowmultiline};
		$U{rejected}=~s/^\s+//;
		$U{rejected}=~s/\s+$//;
	} 
	if($U{message}){
		$U{message}=~s/&(?![\w\d\#]{2,8};)/&amp;/g;
		$U{message}=~s/</&lt;/g;
		$U{message}=~s/>/&gt;/g;
		$U{message}=~s/"/&quot;/g;
		$U{message}=~s/\r\n/<br>/g;
		$U{message}=~s/\n/<br>/g;
		$U{message}=~s/\r/<br>/g;
		$U{message}=~s/<br>(<br>)+/<br><br>/g;
		$U{message}=~s/<br><br>$/<br>/;
		$U{message}=~s/<br>/ /g unless $C{allowmultiline};
		if($C{allowmultiline} and $Q{multi}[0]){
			$U{message}=~s/  / &nbsp;/g;
			$U{message}=~s/<br> /<br>&nbsp;/g;
		}else{
			$U{message}=~s/^\s+//;
			$U{message}=~s/\s+$//;
			$U{message}=~s/\s+/ /g;
		}
	}
	else{
		return
	}
	$U{delstatus}=$U{status};
	$U{displayname}=style_this($U{nickname},$U{fontinfo});
	if($Q{sendto}[0]eq'*'){
		$U{poststatus}='1';
		$C{mesall}=~s/<NICK>/$U{displayname}/;
		$U{displayname}=$C{mesall};
	}
	elsif($Q{sendto}[0]eq'?' and $U{status}>=2){
		$U{poststatus}='2';
		$C{mesmem}=~s/<NICK>/$U{displayname}/;
		$U{displayname}=$C{mesmem};
	}
	elsif($Q{sendto}[0]eq'#' and $U{status}>=6){
		$U{poststatus}='6';
		$C{messtaff}=~s/<NICK>/$U{displayname}/;
		$U{displayname}=$C{messtaff};
	}
	elsif($C{allowpms}){# known nick in room?
		foreach(keys %X){if($Q{sendto}[0]eq$X{$_}[0]){
			$U{recipient}=$_; 
			$U{displayrecp}=style_this($_,$X{$_}[2]);
		}}
		if($U{recipient}){
			$U{poststatus}='9';
			$U{delstatus}='9';
			$C{mespm}=~s/<NICK>/$U{displayname}/;
			$C{mespm}=~s/<RECP>/$U{displayrecp}/;
			$U{displayname}=$C{mespm};
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
}

sub add_message{
	return unless $U{message};
	my %newmessage=(
		postdate  =>$^T,
		postid    =>$U{postid},
		poststatus=>$U{poststatus}, 
		poster    =>$U{nickname},
		recipient =>$U{recipient},
		text      =>$U{displayname}.style_this($U{message},$U{fontinfo}),
		delstatus =>$U{delstatus}
	);
	sysopen(MESSAGES,"$datadir/messages",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (messages/open)");
	flock(MESSAGES,LOCK_EX) or send_error("$I{errfile} (messages/lock)");
	my @lines=<MESSAGES>;
	seek(MESSAGES,0,0) or send_error("$I{errfile} (messages/seek)");
	truncate(MESSAGES,0) or send_error("$I{errfile} (messages/truncate)");
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print MESSAGES $line unless expiredm($temp{postdate});
	}
	print MESSAGES messageline(%newmessage);
	close MESSAGES or send_error("$I{errfile} (messages/close)");
}

sub add_system_message{my($mes,$nick)=@_;
	$U{message}=$mes if $mes; return unless $U{message};
	$nick=style_this($U{nickname},$U{fontinfo}) unless $nick;
	$U{message}=~s/<NICK>/$nick/;
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>'1',
		text=>$U{message},
		delstatus=>'9'
	);
	sysopen(MESSAGES,"$datadir/messages",O_WRONLY|O_APPEND|O_CREAT,0600) or send_error("$I{errfile} (messages/open)");
	flock(MESSAGES,LOCK_EX) or send_error("$I{errfile} (messages/lock)");
	print MESSAGES messageline(%sysmessage);
	close MESSAGES or send_error("$I{errfile} (messages/close)");
}

sub clean_room{
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>'1',
		text=>$C{roomclean},
		delstatus=>'9'
	);
	sysopen(MESSAGES,"$datadir/messages",O_WRONLY|O_TRUNC|O_CREAT,0600) or send_error("$I{errfile} (messages/open)");
	flock(MESSAGES,LOCK_EX) or send_error("$I{errfile} (messages/lock)");
	print MESSAGES messageline(%sysmessage);
	close MESSAGES or send_error("$I{errfile} (messages/close)");
}

sub clean_selected{
	my %mids;foreach(@{$Q{mid}}){$mids{$_}=1}
	sysopen(MESSAGES,"$datadir/messages",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (messages/open)");
	flock(MESSAGES,LOCK_EX) or send_error("$I{errfile} (messages/lock)");
	my @lines=<MESSAGES>;
	seek(MESSAGES,0,0) or send_error("$I{errfile} (messages/seek)");
	truncate(MESSAGES,0) or send_error("$I{errfile} (messages/truncate)");
	while(my $line=shift@lines){
		my %temp=messagehash($line);
		print MESSAGES $line unless(expiredm($temp{postdate}) or $mids{$temp{postdate}.$temp{postid}});
	}
	close MESSAGES or send_error("$I{errfile} (messages/close)");
}

sub del_last_message{
	sysopen(MESSAGES,"$datadir/messages",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (messages/open)");
	flock(MESSAGES,LOCK_EX) or send_error("$I{errfile} (messages/lock)");
	my @lines=<MESSAGES>;
	seek(MESSAGES,0,0) or send_error("$I{errfile} (messages/seek)");
	truncate(MESSAGES,0) or send_error("$I{errfile} (messages/truncate)");
	for(my$i=@lines;$i>=0;$i--){
		my %temp=messagehash($lines[$i]);
		if($U{nickname}eq$temp{poster}){
			splice(@lines,$i,1);
			last;
		}
	}
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print MESSAGES $line unless expiredm($temp{postdate});
	}
	close MESSAGES or send_error("$I{errfile} (messages/close)");
}

sub del_all_messages{
	my $nick=$_[0];$nick=$U{nickname} unless $nick;
	sysopen(MESSAGES,"$datadir/messages",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (messages/open)");
	flock(MESSAGES,LOCK_EX) or send_error("$I{errfile} (messages/lock)");
	my @lines=<MESSAGES>;
	seek(MESSAGES,0,0) or send_error("$I{errfile} (messages/seek)");
	truncate(MESSAGES,0) or send_error("$I{errfile} (messages/truncate)");
	while(my $line=shift@lines){
		my %temp=messagehash($line);
		print MESSAGES $line unless(expiredm($temp{postdate}) or $temp{poster}eq$nick);
	}
	close MESSAGES or send_error("$I{errfile} (messages/close)");
}

sub print_messages{
	sysopen(MESSAGES,"$datadir/messages",O_RDONLY)  or return;
	flock(MESSAGES,LOCK_SH) or return;
	my @lines=<MESSAGES>;
	close MESSAGES;
	while(my $line=pop@lines){
		my %message=messagehash($line);
		if($U{status}>=$message{poststatus} or $U{nickname}eq$message{poster} or $U{nickname}eq$message{recipient}){ 
			print "$message{text}<br>" unless expiredm($message{postdate});  
		}
	}
}

sub print_select_messages{
	sysopen(MESSAGES,"$datadir/messages",O_RDONLY)  or return;
	flock(MESSAGES,LOCK_SH) or return;
	my @lines=<MESSAGES>;
	close MESSAGES;
	while(my $line=pop@lines){
		my %message=messagehash($line);
		if($U{status}>$message{delstatus}){ 
			print qq|<input type="checkbox" name="mid" id="$message{postdate}$message{postid}" value="$message{postdate}$message{postid}"><label for="$message{postdate}$message{postid}"> $message{text}</label><br>|unless expiredm($message{postdate});
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
# installation and initialisation routines
######################################################################

sub load_config{
	set_internal_defaults();
	if(-e"$datadir/language"){# load language file
		sysopen(LANG,"$datadir/language",O_RDONLY) or send_fatal("$I{errfile} (language/open)");
		flock(LANG,LOCK_SH) or send_fatal("$I{errfile} (language/lock)");
		while(<LANG>){
			next unless /^[0-9a-f]/;
			my($ikey,$ival)=split('l',$_);
			$I{pack('H*',$ikey)}=pack('H*',$ival);
			last if($I{stop_action}=~/-$Q{action}[0]-/);# only load what we need
		}
		close LANG;
	}
	set_config_defaults();
	sysopen(CONFIG,"$datadir/config",O_RDONLY) or send_fatal("$I{errfile} (config/open)");
	flock(CONFIG,LOCK_SH) or send_fatal("$I{errfile} (config/lock)");
	while(<CONFIG>){
		next unless /^[0-9a-f]/;
		my($ckey,$cval)=split('l',$_);
		$C{pack('H*',$ckey)}=pack('H*',$cval);
		last if($C{stop_action}=~/-$Q{action}[0]-/);# only load what we need
	}
	close CONFIG;
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	$I{suerrbadnick}=~s/<MAX>/$C{maxname}/;
	$I{suerrbadpass}=~s/<MIN>/$C{minpass}/;
	$I{setsuhelp}=~s/<DATA>/$datadir/;
	set_html_vars();
}

sub save_config{
	sysopen(CONFIG,"$datadir/config",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (config/open)");
	flock(CONFIG,LOCK_EX) or send_error("$I{errfile} (config/lock)");
	seek(CONFIG,0,0) or send_error("$I{errfile} (config/seek)");
	truncate(CONFIG,0) or send_error("$I{errfile} (config/truncate)");
	foreach(qw(redirifsusp redirtourl title kickederror coltxt colbg collnk colvis colact sessionexpire guestsexpire messageexpire waitingexpire kickpenalty defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidth boxheight allowmultiline allowfonts allowpms cssglobal styleback csserror cssview csswait stylecheckwait stylewaitrel roomentry))
		{print CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print CONFIG unpack('H*','stop_action'),'l',unpack('H*','-view-wait-'),"l\n";
	foreach(qw(mesall mesmem mespm messtaff csspost styleposttext stylepostsend stylesendlist styledellast styledelall styleswitch))
		{print CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print CONFIG unpack('H*','stop_action'),'l',unpack('H*','-post-delete-'),"l\n";
	foreach(qw(header footer noguests rndguestcol loginbutton nowchatting csslogin stylelogintext stylecolselect styleenter tableattributes frameattributes))
		{print CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print CONFIG unpack('H*','stop_action'),'l',unpack('H*','--'),"l\n";
	foreach(qw(csscontrols stylerelpost stylerelmes styleprofile styleadmin stylerules styleexit cssprofile))
		{print CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print CONFIG unpack('H*','stop_action'),'l',unpack('H*','-controls-profile-colours-'),"l\n";
	foreach(qw(rulestxt entrymessage roomexit logoutmessage roomclean))
		{print CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print CONFIG unpack('H*','stop_action'),'l',unpack('H*','-help-entry-login-logout-'),"l\n";
	foreach(qw(regmessage kickedmessage styledelsome cssadmin lastchangedby lastchangedat))
		{print CONFIG unpack('H*',$_),'l',unpack('H*',$C{$_}),"l\n"}print CONFIG unpack('H*','stop_action'),'l',unpack('H*',''),"l\n";
	close CONFIG or send_error("$I{errfile} (config/close)");
}

sub set_config{
	foreach(keys %C){
		$C{$_}=$Q{$_}[0];
		$C{$_}=~s/&quot;/"/g;
		$C{$_}=~s/&lt;/</g;
		$C{$_}=~s/&gt;/>/g;
		$C{$_}=~s/&amp;/&/g;
		$C{$_}=~s/\r\n/\n/g;
		$C{$_}=~s/\r/\n/g;
	}
	$C{lastchangedby}=$U{nickname};
	$C{lastchangedat}=get_timestamp();
}

sub get_config_backup{
	require MIME::Base64;
	MIME::Base64->import(qw(encode_base64));
	my $blob='';
	sysopen(CONFIG,"$datadir/config",O_RDONLY) or return "$I{errfile} (config/open)";
	flock(CONFIG,LOCK_SH) or return "$I{errfile} (config/lock)";
	while(<CONFIG>){$blob.=$_.'n'}
	close CONFIG;
	$blob=~s/[^a-f0-9ln]//gi;
	$blob.='h'.hash_this($blob).'hiCONFIGi';
	$blob="-----BEGIN LE CHAT CONFIG-----\n".get_timestamp((stat("$datadir/config"))[9])." - $C{title}\n\n".encode_base64($blob).'-----END LE CHAT CONFIG-----';
	return $blob;
}

sub get_members_backup{
	require MIME::Base64;
	MIME::Base64->import(qw(encode_base64));
	my $blob='';
	sysopen(MEMBERS,"$datadir/members",O_RDONLY) or return "$I{errfile} (members/open)";
	flock(MEMBERS,LOCK_SH) or return "$I{errfile} (members/lock)";
	while(<MEMBERS>){$blob.=$_.'n'}
	close MEMBERS;
	$blob=~s/[^a-f0-9ln]//gi;
	$blob.='h'.hash_this($blob).'hiMEMBERSi';
	$blob="-----BEGIN LE CHAT MEMBERS-----\n".get_timestamp((stat("$datadir/members"))[9])." - $C{title}\n\n".encode_base64($blob).'-----END LE CHAT MEMBERS-----';
	return $blob;
}

sub get_language_backup{
	require MIME::Base64;
	MIME::Base64->import(qw(encode_base64));
	my $blob='';
	sysopen(LANG,"$datadir/language",O_RDONLY) or return "$I{errfile} (language/open)";
	flock(LANG,LOCK_SH) or return "$I{errfile} (language/lock)";
	while(<LANG>){$blob.=$_.'n'}
	close LANG;
	$blob=~s/[^a-f0-9ln]//gi;
	$blob.='h'.hash_this($blob).'hiLANGUAGEi';
	$blob="-----BEGIN LE CHAT LANGUAGE-----\n"."Language: $I{language} Charset: $I{charset}\n\n".encode_base64($blob).'-----END LE CHAT LANGUAGE-----';
	return $blob;
}

sub get_restore_results{
	$_[0]=$Q{backupdata}[0] unless $_[0];
	$_[0]=~s/\r\n/<br>/g;
	$_[0]=~s/\n/<br>/g;
	$_[0]=~s/\r/<br>/g;
	$_[0]=~s/<br>/\n/g;
	my $result='';
	(my $memb)=$_[0]=~/-----BEGIN LE CHAT MEMBERS-----[\w\W]*?\n\n([\w\W]*)-----END LE CHAT MEMBERS-----/;
	(my $conf)=$_[0]=~/-----BEGIN LE CHAT CONFIG-----[\w\W]*?\n\n([\w\W]*)-----END LE CHAT CONFIG-----/;
	(my $lang)=$_[0]=~/-----BEGIN LE CHAT LANGUAGE-----[\w\W]*?\n\n([\w\W]*)-----END LE CHAT LANGUAGE-----/;
	return $I{invalidbackup} unless($memb or $conf or $lang);
	$result.=restore_members($memb)."\n"if$memb;
	$result.=restore_config($conf)."\n"if$conf;
	$result.=restore_language($lang)."\n"if$lang;
	return $result;
}

sub restore_members{
	require MIME::Base64;
	MIME::Base64->import(qw(decode_base64));
	my $memb=decode_base64($_[0]);
	my($blob,$hash,$info)=$memb=~/^([a-f0-9ln]+)h([a-f0-9]+)hi([A-Z]+)i$/;
	if(hash_this($blob)eq$hash and 'MEMBERS'eq$info){
		$blob=~tr/n/\n/s;
		sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600) or return "$I{memrestfail} $I{errfile} (members/open)";
		flock(MEMBERS,LOCK_EX) or return "$I{memrestfail} $I{errfile} (members/lock)";
		seek(MEMBERS,0,0) or return "$I{memrestfail} $I{errfile} (members/seek)";
		truncate(MEMBERS,0) or return "$I{memrestfail} $I{errfile} (members/truncate)";
		print MEMBERS $blob;
		close MEMBERS or return "$I{memrestfail} $I{errfile} (members/close)";
		return $I{memrestsucc};
	}
	else{
		return $I{memrestinvalid};
	}
}

sub restore_config{
	require MIME::Base64;
	MIME::Base64->import(qw(decode_base64));
	my $conf=decode_base64($_[0]);
	my($blob,$hash,$info)=$conf=~/^([a-f0-9ln]+)h([a-f0-9]+)hi([A-Z]+)i$/;
	if(hash_this($blob)eq$hash and 'CONFIG'eq$info){
		$blob=~tr/n/\n/s;
		sysopen(CONFIG,"$datadir/config",O_RDWR|O_CREAT,0600) or return "$I{cfgrestfail} $I{errfile} (config/open)";
		flock(CONFIG,LOCK_EX) or return "$I{cfgrestfail} $I{errfile} (config/lock)";
		seek(CONFIG,0,0) or return "$I{cfgrestfail} $I{errfile} (config/seek)";
		truncate(CONFIG,0) or return "$I{cfgrestfail} $I{errfile} (config/truncate)";
		print CONFIG $blob;
		close CONFIG or return "$I{cfgrestfail} $I{errfile} (config/close)";
		load_config();
		return $I{cfgrestsucc};
	}
	else{
		return $I{cfgrestinvalid};
	}
}

sub restore_language{
	require MIME::Base64;
	MIME::Base64->import(qw(decode_base64));
	my $lang=decode_base64($_[0]);
	my($blob,$hash,$info)=$lang=~/^([a-f0-9ln]+)h([a-f0-9]+)hi([A-Z]+)i$/;
	if(hash_this($blob)eq$hash and 'LANGUAGE'eq$info){
		$blob=~tr/n/\n/s;
		sysopen(LANG,"$datadir/language",O_RDWR|O_CREAT,0600) or return "$I{lngrestfail} $I{errfile} (language/open)";
		flock(LANG,LOCK_EX) or return "$I{lngrestfail} $I{errfile} (language/lock)";
		seek(LANG,0,0) or return "$I{lngrestfail} $I{errfile} (language/seek)";
		truncate(LANG,0) or return "$I{lngrestfail} $I{errfile} (language/truncate)";
		print LANG $blob;
		close LANG or return "$I{lngrestfail} $I{errfile} (language/close)";
		load_config();
		return $I{lngrestsucc};
	}
	else{
		return $I{lngrestinvalid};
	}
}

sub change_admin_status{
	my $err;my %temp;
	return $I{errnonick} unless $Q{admnick}[0];
	return $I{errbaddata} unless $Q{what}[0]=~/^new|up|down$/;
	if($Q{what}[0]eq'new'){
		return $I{errbadnick} unless valid_nick($Q{admnick}[0]);
		return $I{errbadpass} unless valid_pass($Q{admpass}[0]);
		$Q{admnick}[0]=unpack('H*',$Q{admnick}[0]);
	}
	sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600) or send_error("$I{errfile} (members/open)");
	flock(MEMBERS,LOCK_EX) or send_error("$I{errfile} (members/lock)");
	my @lines=<MEMBERS>;
	#backup_members(@lines);
	seek(MEMBERS,0,0) or send_error("$I{errfile} (members/seek)");
	truncate(MEMBERS,0) or send_error("$I{errfile} (members/truncate)");
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
			print MEMBERS memberline(%temp);
		}
		else{
			print MEMBERS $_;
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
		print MEMBERS memberline(%temp);
		$err=$I{newmainreg};
		$err=~s/<NICK>/$temp{nickname}/;
	}
	close MEMBERS or send_error("$I{errfile} (members/close)");
	return $err;
}

sub set_config_defaults{
	%C=(# default user configuration
		lastchangedby =>'-',
		lastchangedat =>'-',
		# redirect
		redirifsusp   =>'0',
		redirtourl    =>'',
		# text
		title         =>"$I{ctitle}",
		header        =>"$I{cheader}",
		footer        =>"$I{cfooter}",
		noguests      =>"$I{cnoguests}",
		rndguestcol   =>"$I{crndguestcol}",
		loginbutton   =>"$I{cloginbutton}",
		rulestxt      =>"$I{crulestxt}",
		entrymessage  =>"$I{centrymessage}",
		logoutmessage =>"$I{clogoutmessage}",
		kickederror   =>"$I{ckickederror}",
		roomentry     =>"$I{croomentry}",
		roomexit      =>"$I{croomexit}",
		regmessage    =>"$I{cregmessage}",
		kickedmessage =>"$I{ckickedmessage}",
		roomclean     =>"$I{croomclean}",
		nowchatting   =>"$I{cnowchatting}",
		# message enclosures
		mesall        =>"$I{cmesall}",
		mesmem        =>"$I{cmesmem}",
		mespm         =>"$I{cmespm}",
		messtaff      =>"$I{cmesstaff}",
		# data
		sessionexpire =>'15',
		guestsexpire  =>'10',
		messageexpire =>'10',
		waitingexpire =>'5',
		kickpenalty   =>'10',
		defaultrefresh=>'20',
		minrefresh    =>'15',
		maxrefresh    =>'150',
		maxmessage    =>'1000',
		maxname       =>'20',
		minpass       =>'10',
		floodlimit    =>'1',
		boxwidthdef   =>'40',
		boxheightdef  =>'3',
		# default colors for body and non-CSS browsers
		coltxt        =>'FFFFFF',
		colbg         =>'000000',
		collnk        =>'6666FF',
		colvis        =>'FF66FF',
		colact        =>'FF0033',     
		# styles
		cssglobal     =>'input,select,textarea{color:#FFFFFF;background-color:#000000}',
		styleback     =>'background-color:#004400;color:#FFFFFF',
		cssview       =>'',
		styledelsome  =>'background-color:#660000;color:#FFFFFF',
		stylecheckwait=>'background-color:#660000;color:#FFFFFF',
		csswait       =>'',
		stylewaitrel  =>'',
		csspost       =>'',
		styleposttext =>'',
		stylepostsend =>'',
		stylesendlist =>'',
		styledellast  =>'',
		styledelall   =>'',
		styleswitch   =>'',
		csscontrols   =>'',
		stylerelpost  =>'',
		stylerelmes   =>'',
		styleprofile  =>'',
		styleadmin    =>'',
		stylerules    =>'',
		styleexit     =>'',
		csslogin      =>'',
		stylelogintext=>'',
		stylecolselect=>'',
		styleenter    =>'',
		csserror      =>'body{color:#FF0033}',
		cssprofile    =>'',
		cssadmin      =>'',
		# layout
		tableattributes=>'border="1"',
		frameattributes=>'border="3" frameborder="3" framespacing="3"',
		# options
		allowmultiline=>'1',
		allowfonts    =>'1',
		allowpms      =>'1',
	);
}

sub set_internal_defaults{

	%F=(# fonts. TODO: review these and choose some cross-platform friendly items
		'Arial'          =>' face="Arial,Helvetica,sans-serif"',
		'Book Antiqua'   =>' face="Book Antiqua,MS Gothic"',
		'Comic'          =>' face="Comic Sans MS,Papyrus"', 
		'Comic small'    =>' face="Comic Sans MS,Papyrus" size="-1"',
		'Courier'        =>' face="Courier New,Courier,monospace"',
		'Cursive'        =>' face="Cursive,Papyrus"',
		'Fantasy'        =>' face="Fantasy,Futura,Papyrus,"',
		'Garamond'       =>' face="Garamond,Palatino,serif"',
		'Georgia'        =>' face="Georgia,Times New Roman,Times,serif"',
		'Serif'          =>' face="MS Serif,New York,serif"',
		'System'         =>' face="System,Chicago,sans-serif"',
		'Times New Roman'=>' face="Times New Roman,Times,serif"',
		'Verdana'        =>' face="Verdana,Geneva,Arial,Helvetica,sans-serif"',
		'Verdana small'  =>' face="Verdana,Geneva,Arial,Helvetica,sans-serif" size="-1"'
	);

	# internal messages
	%I=(
		# all occasions
		language      =>'english',
		charset       =>'iso-8859-1', 
		backtologin   =>'Back to the login page.',
		# login page:
		nickname      =>'Nickname',
		password      =>'Password',
		selcolguests  =>'Guests, choose a colour:',
		selcoldefault =>'Room Default',
		selcolrandom  =>'Random Colour',
		# suspended page
		suspended     =>'Suspended',
		susptext      =>'This chat is currently not available. Please try again later!',
		redirtext     =>'Please try this alternate address!',
		# messages frame
		members       =>'Members:',
		guests        =>'Guests:',
		butcheckwait  =>'Check <COUNT> Newcomer(s)',
		# error messages
		error         =>'Error: ',
		errfile       =>'file error',
		errexpired    =>'invalid/expired session',
		erraccdenied  =>'access denied',
		errnoguests   =>'no guests allowed at this time',
		# config default text
		ctitle        =>'LE CHAT',
		cheader       =>'<h1>LE CHAT</h1>Your IP address is <IP><br><br>',
		cfooter       =>"<small>LE CHAT - $version</small>",
		cnoguests     =>'Only members at this time!',
		crndguestcol  =>'1',
		cloginbutton  =>'Enter LE CHAT',
		crulestxt     =>'Just be nice!',
		centrymessage =>'Welcome <NICK> to LE CHAT',
		clogoutmessage=>'Bye <NICK>, visit again soon!',
		ckickederror  =>'<NICK>, you have been kicked out of LE CHAT!',
		croomentry    =>'<NICK> enters LE CHAT!',
		croomexit     =>'<NICK> leaves LE CHAT.',
		cregmessage   =>'<NICK> is now a registered member of LE CHAT.',
		ckickedmessage=>'<NICK> has been kicked out of LE CHAT!',
		croomclean    =>'LE CHAT was cleaned.',
		cnowchatting  =>'Currently <COUNT> chatter(s) in room:<br><NAMES>',
		cmesall       =>'<NICK> &#62; ',
		cmesmem       =>'<NICK> &#62;&#62; ',
		cmespm        =>'<font color=white>[PM to <RECP>]</font> <NICK> &#62;&#62; ',
		cmesstaff     =>'<font color=white>[Staff]</font> <NICK> &#62;&#62; ',
		# colour names
		Beige      =>'beige',
		Black      =>'black',
		Blue       =>'blue',
		BlueViolet =>'blue violet',
		Brown      =>'brown',
		Cyan       =>'cyan',
		DarkBlue   =>'dark blue',
		DarkGreen  =>'dark green',
		DarkRed    =>'dark red',
		DarkViolet =>'dark violet',
		DeepSkyBlue=>'sky blue',
		Gold       =>'gold',
		Grey       =>'grey',
		Green      =>'green',
		HotPink    =>'hot pink',
		Indigo     =>'indigo',
		LightBlue  =>'light blue',
		LightGreen =>'light green',
		LimeGreen  =>'lime green',
		Magenta    =>'magenta',
		Olive      =>'olive',
		Orange     =>'orange',
		OrangeRed  =>'orange red',
		Purple     =>'purple',
		Red        =>'red',
		RoyalBlue  =>'royal blue',
		SeaGreen   =>'sea green',
		Sienna     =>'sienna',
		Silver     =>'silver',
		Tan        =>'tan',
		Teal       =>'teal',
		Violet     =>'violet',
		White      =>'white',
		Yellow     =>'yellow',
		YellowGreen=>'yellow green'
	);
	return if($Q{action}[0]=~/^$|^view$/);
	%I=(%I,
		# post box frame
		butsendto     =>'talk to',
		seltoall      =>'all chatters',
		seltomem      =>'members only',
		seltoadmin    =>'staff only',
		butdellast    =>'delete last message',
		butdelall     =>'delete all messages',
		butmultiline  =>'switch to multi line',
		butsingleline =>'switch to single line',
	);
	return if($Q{action}[0]=~/^(post|delete)$/);
	%I=(%I,
		frames        =>'This chat uses <b>frames</b>. Please enable frames in your browser or use a suitable one!',
		# waiting room
		waitroom      =>'Waiting Room',
		waitmessage   =>q|Welcome <NICK>, please be patient until an admin will let you into the chat room.<br><br>If this page doesn't refresh every <REFRESH> seconds, use the button below to reload it manually!|,
		butreloadw    =>'Reload Page',
		# various occasions
		backtochat    =>'Back to the chat.',
		minutes       =>'minutes',
		seconds       =>'seconds', 
		savechanges   =>'save changes',
		# error messages
		errbadnick    =>'invalid nickname (1-<MAX> characters, no special characters allowed)',
		errnonick     =>'No nickname given.',
		errexistnick  =>'Nick exists already.',
		erraccdenied  =>'access denied',
		errbadpass    =>'invalid password (<MIN> characters required)',
		errbadlogin   =>'invalid nickname/password',
		errbaddata    =>'Invalid data received.',
		errcantreg    =>'cannot register "<NICK>"',
		errcantregnew =>'cannot register new member "<NICK>"',
		errcantkick   =>'cannot kick "<NICK>"',
		erralreadyreg =>'"<NICK>" is already registered.',
		errcantstatus =>'cannot change status of "<NICK>"',
		# entry page
		entryhelp     =>q|If this frame does not reload in <REFRESH> seconds, you'll have to enable automatic redirection (meta refresh) in your browser. Also make sure no web filter, local proxy tool or browser plugin is preventing automatic refreshing! This could be for example "Polipo", "NoScript", "TorButton", "Proxomitron", etc. just to name a few.<br>As a workaround (or in case of server/proxy reload errors) you can always use the buttons at the bottom to refresh manually.|,
	);
	return if($Q{action}[0]=~/^(wait|login|entry|logout)$/);
	%I=(%I,
		# controls frame
		butreloadp    =>'Reload Post Box',
		butreloadm    =>'Reload Messages',
		butprofile    =>'Change Profile',
		butadmin      =>'Admin',
		butrules      =>'Rules &amp; Help',
		butexit       =>'Exit Chat',
	);
	return if($Q{action}[0]=~/^controls$/);
	%I=(%I,
		# profile page
		profileheader =>'Your Profile',
		refreshrate   =>'Refresh rate',
		entryrefresh  =>'Entry page delay',
		fontcolour    =>'Font colour',
		viewcolours   =>'view examples',
		fontface      =>'Font face',
		fontbold      =>'bold',
		fontitalic    =>'italic',
		fontexample   =>'take that as example for your chosen font',
		boxsizes      =>'Post box size',
		boxwidth      =>'width',
		boxheight     =>'height',
		changepass    =>'Change Password',
		oldpass       =>'old password',
		newpass       =>'new password',
		confirmpass   =>'confirm new password',
		succchanged   =>'Your profile was successfully saved.',
		errdiffpass   =>'Password confirmation does not match.',
		errwrongpass  =>'Password is wrong.',
		# colourtable
		colheader     =>'Colourtable',
		backtoprofile =>'Back to your profile.',
	);
	return if($Q{action}[0]=~/^(profile|colours)$/);
	%I=(%I,
		# rules and help page
		rules         =>'Rules',
		help          =>'Help',
		helpguests    =>q|All functions should be pretty much self-explaining, just use the buttons. In your profile you can adjust the refresh rate, font colour and your preferred input box size.<br><u>Note:</u> This is a chat, so if you don't keep talking, you will be automatically logged out after a while.|,
		helpregs      =>q|<br>Members: You'll have some more options in your profile. You can adjust your font face, specify how long the entry page will be shown and you can change your password anytime.|,
		helpmods      =>q|<br>Moderators: Notice the Admin-button at the bottom. It'll bring up a page where you can clean the room, kick chatters, view all active sessions and disable guest access completely if needed.|,
		helpadmins    =>q|<br>Admins: You'll be furthermore able to set all the guest access options, register guests, edit members and register new nicks without them beeing in the room.|,
	);
	return if($Q{action}[0]=~/^help$/);
	%I=(%I,
		# admin waiting room/sessions
		admwaiting    =>'Newcomers in Waiting Room',
		admsessions   =>'Active Sessions',
		timeoutin     =>'Timeout&nbsp;in',
		ip            =>'IP-Number',
		useragent     =>'Browser-Identification',
		allowchecked  =>'allow checked',
		allowall      =>'allow all',
		denychecked   =>'deny checked',
		denyall       =>'deny all',
		waitempty     =>'No more entry requests to approve.',
		# admin page
		admheader     =>'Administrative Functions',
		admclean      =>'Clean Messages',
		admcleanall   =>'whole room',
		admcleansome  =>'selection',
		admkick       =>'Kick Chatter',
		admkickpurge  =>'also purge messages',
		admvsessions  =>'View Active Sessions',
		admguests     =>'Guest Access',
		admguestsoff  =>'always forbid',
		admguestson   =>'always allow',
		admguestsauto =>'allow while an admin is present',
		admguestsbell =>'require admin approval for entry',
		admregguest   =>'Register Guest',
		admmembers    =>'Members',
		admregnew     =>'Register New Member',
		selmemdelete  =>'delete from file',
		selmemdeny    =>'deny access',
		selmemreg     =>'set to regular',
		selmemmod     =>'set to moderator',
		selmemadmin   =>'set to admin',
		selchoose     =>'(choose)',
		symdenied     =>'(!)',
		symguest      =>'(G)',
		symmod        =>'(M)',
		symadmin      =>'(A)',
		butadmdo      =>'do',
		butadmclean   =>' clean ',
		butadmkick    =>'  kick  ',
		butadmview    =>'  view  ',
		butadmset     =>'   set   ',
		butadmreg     =>'register',
		butadmstatus  =>'change',
		butadmregnew  =>'register',
		# clean some
		butdelsome    =>'delete selected messages',
		# admin messages
		succreg       =>'"<NICK>" successfully registered.',
		succstatus    =>'Status of "<NICK>" successfully changed.',
		succdelmem    =>'"<NICK>" successfully deleted from file.',
	);
	return if($Q{action}[0]=~/^admin$/);
	%I=(%I,#
		# setup login
		aloginname     =>'name',
		aloginpass     =>'pass',
		aloginbut      =>'login',
		# descriptions on setup page
		chatsetup      =>'Chat Setup',
		chataccess     =>'Chat Access',
		suspend        =>'suspended',
		enabled        =>'enabled',
		butset         =>'set',
		backups        =>'Backups',
		backmem        =>'Backup members',
		backcfg        =>'Backup configuration',
		restore        =>'Restore backup',
		backdat        =>'Backup data to copy/paste.',
		mainadmins     =>'Main Admins',
		regadmin       =>'Register new Main Admin',
		raiseadmin     =>'Raise to Main Admin',
		loweradmin     =>'Lower to Regular Admin',
		butregadmin    =>'register',
		butraise       =>'  raise  ',
		butlower       =>'  lower  ',
		cfgsettings    =>'Change Configuration Settings',
		cfgmainadm     =>'Log in with your main admin nick instead of the superuser to change particular chat settings!',
		resetlanguage  =>'Reset language to the default (english).',
		# redirection
		redirifsusp    =>'Redirect to alternate URL if suspended',
		redirtourl     =>'Redirection URL',
		# options
		allowfonts     =>'Allow change of font face',
		allowmultiline =>'Allow multiline messages',
		allowpms       =>'Allow private messages',
		rndguestcol    =>'Randomise default colour for guests',
		yes            =>'yes',
		no             =>'no',
		# values
		sessionexpire  =>'Minutes of silence until member session expires',
		guestsexpire   =>'Minutes of silence until guest session expires',
		messageexpire  =>'Minutes until messages get removed',
		kickpenalty    =>'Minutes nickname is blocked after beeing kicked',
		waitingexpire  =>'Minutes until guest entry requests expire',
		defaultrefresh =>'Default refresh time (seconds)',
		minrefresh     =>'Minimum refresh time (seconds)',
		maxrefresh     =>'Maximum refresh time (seconds)',
		floodlimit     =>'Minimum time between posts from same nick (seconds)',
		boxwidthdef    =>'Default post box width',
		boxheightdef   =>'Default post box height',
		maxmessage     =>'Maximum message length',
		maxname        =>'Maximum characters for nickname',
		minpass        =>'Minimum characters for password',
		# text
		title          =>'Browser title / name of the chat',
		noguests       =>'Text if no guests allowed',
		loginbutton    =>'Login button text',
		header         =>'Login page header (&lt;IP&gt; shows users IP-address)',
		footer         =>'Login page footer (&lt;IP&gt; shows users IP-address)',
		rulestxt       =>'Rules (&lt;IP&gt; shows users IP-address)',
		nowchatting    =>'Now chatting (&lt;NAMES&gt;=list, &lt;COUNT&gt;=number)',
		entrymessage   =>'Entry message (use &lt;NICK&gt; for name)',
		logoutmessage  =>'Logout message (use &lt;NICK&gt; for name)',
		kickederror    =>'Kicked error message (use &lt;NICK&gt; for name)',
		roomentry      =>'Entry notification (use &lt;NICK&gt; for name)',
		roomexit       =>'Exit notification (use &lt;NICK&gt; for name)',
		regmessage     =>'Register notification (use &lt;NICK&gt; for name)',
		kickedmessage  =>'Kick notification (use &lt;NICK&gt; for name)',
		roomclean      =>'Cleaning message',
		# message enclosures
		mesall      =>'Message to all (use &lt;NICK&gt; for name)',
		mesmem      =>'Message to members (use &lt;NICK&gt; for name)',
		mespm       =>'Private Messages (&lt;NICK&gt;=poster, &lt;RECP&gt;=recipient)',
		messtaff    =>'Staff Messages (use &lt;NICK&gt; for name)',
		# layout
		tableattributes=>'table attributes login page',
		frameattributes=>'frame attributes',
		# default colors for body and non-CSS browsers
		colbg          =>'Background colour',
		coltxt         =>'Text colour',
		collnk         =>'Link colour',
		colvis         =>'Visited link colour',
		colact         =>'Active link colour',
		# styles
		cssglobal      =>'CSS for all pages',
		csslogin       =>'CSS login page',
		stylelogintext =>'textfield style',
		stylecolselect =>'selection style',
		styleenter     =>'login button style',  
		csspost        =>'CSS post frame',
		styleposttext  =>'post text style',
		stylepostsend  =>'send button style',
		stylesendlist  =>'send list style',
		styledellast   =>'delete last button',
		styledelall    =>'delete all button',
		styleswitch    =>'multiline button',  
		cssview        =>'CSS messages frame',
		styledelsome   =>'delete selected button',
		stylecheckwait =>'check newcomers button',
		csswait        =>'CSS waiting room',
		stylewaitrel   =>'waiting room reload button',
		csscontrols    =>'CSS controls frame',
		stylerelpost   =>'reload post box',
		stylerelmes    =>'reload messages',
		styleprofile   =>'profile button',
		styleadmin     =>'admin button',
		stylerules     =>'rules button',
		styleexit      =>'exit button',
		cssprofile     =>'CSS profile page', 
		cssadmin       =>'CSS admin pages',
		csserror       =>'CSS error pages',
		styleback      =>'back button style',
		lastchanged    =>'Last changed:',
		butsavecfg     =>'save configuration',
		butlogout      =>'log out',
		# initialisation stuff
		invalidbackup  =>'No valid backup data given.',
		memrestfail    =>'Restoring members failed:',
		memrestsucc    =>'Restoring members succeeded.',
		memrestinvalid =>'Invalid data for members file.',
		cfgrestfail    =>'Restoring configuration failed:',
		cfgrestsucc    =>'Restoring configuration succeeded.',
		cfgrestinvalid =>'Invalid data for configuration file.',
		lngrestfail    =>'Restoring language failed:',
		lngrestsucc    =>'Restoring language succeeded.',
		lngrestinvalid =>'Invalid data for language file.',
		raisemainsucc  =>'"<NICK>" raised to main admin.',
		raisemaindone  =>'"<NICK>" is already main admin.',
		raisemainfail  =>'"<NICK>" is not an admin.',
		lowerregsucc   =>'"<NICK>" lowered to regular admin.',
		lowerregdone   =>'"<NICK>" is already regular admin.',
		lowerregfail   =>'"<NICK>" is not an admin.',
		newmainreg     =>'New main admin "<NICK>" registered.',
		initsetup      =>'Initial Setup',
		setsu          =>'Superuser Login',
		setsunick      =>'Superuser Nick:',
		setsupass      =>'Superuser Pass:',
		setsupassconf  =>'Confirm Pass:',
		setsuhelp      =>'In case of file corruption on the server, you can still restore backups with your superuser nick. You will also need it to install main admins who will be able to make changes to the chat setup, suspend/unsuspend the chat and upgrade members to moderators and regular admins.<br>You can not alter your superuser login later, so choose a secret nick and a very strong pass here. Take a nick that will not show up in the chat room. If you ever need to reset the superuser, you will have to delete the file <nobr>&quot;<DATA>/admin&quot;</nobr> on the server and do this setup here again.<br><br><br>',
		initback       =>'Restore Backups',
		initbackhelp   =>'If you want to recover files (members, config, language) from existing backup data, paste it all here:',
		initbut        =>'initialise chat',
		suerrunknown   =>'Unknown error.',
		suerrfileexist =>'A superuser file exists already!',
		suerrbadnick   =>'Invalid nickname for superuser (1-<MAX> characters, no special characters allowed). Try again!',
		suerrbadpass   =>'Password too short, <MIN> characters required. Try again!',
		suerrbadpassc  =>'Password confirmation does not match. Try again!',
		suwritesucc    =>'Superuser file was written successfully.',
		suwritefail    =>'File was not written correctly. Please try again!',
		initgotosetup  =>'Go to Setup-Page',
	);
}

sub set_html_vars{
	%H=(# default HTML
		begin_html   =>qq|\n<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">\n<html>\n|,
		begin_frames =>qq|\n<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Frameset//EN">\n<html>\n|,
		begin_body   =>qq|\n<body bgcolor="#$C{colbg}" text="#$C{coltxt}" link="#$C{collnk}" alink="#$C{colact}" vlink="#$C{colvis}">\n|,
		end_body     =>"\n</body>",
		end_html     =>"\n</html>\n<!-- LE CHAT $version ($lastchanged) -->\n",
		meta_html    =>qq|\n<title>$C{title}</title>\n<meta name="robots" content="noindex">\n<meta http-equiv="Content-Type" content="text/html; charset=$I{charset}">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="expires" content="0">|,
		add_css      =>'',
		backtologin  =>qq|<table border=0><tr><form action="$S" method="post" target="_parent"><td><input type="submit" value="$I{backtologin}" class="back"></td></form></tr></table>|,
		backtochat   =>qq|<table border=0><tr><form action="$S" method="post" target="view"><input type="hidden" name="action" value="view"><input type="hidden" name="session" value="$Q{session}[0]"><td><input type="submit" value="$I{backtochat}" class="back"></td></form></tr></table>|,
		backtoprofile=>qq|<table border=0><tr><form action="$S" method="post" target="view"><input type="hidden" name="action" value="profile"><input type="hidden" name="session" value="$Q{session}[0]"><td><input type="submit" value="$I{backtoprofile}" class="back"></td></form></tr></table>|
	);
	############################################################
	# add banner killers and other adaptions for known servers #
	# to be updated regularly... tell me your favourite hosts! #
	############################################################
	if($ENV{'SERVER_NAME'}=~m/\.tok2\.com/){
		$H{begin_body}='<noembed><noframes><noscript><body></noscript></noframes></noembed>'.$H{begin_body};
		$H{end_body}='<noembed><noframes><noscript>'.$H{end_body};
		$ENV{'REMOTE_ADDR'}=$ENV{'HTTP_X_FORWARDED_FOR'}if($ENV{'REMOTE_ADDR'}eq$ENV{'SERVER_ADDR'}and$ENV{'HTTP_X_FORWARDED_FOR'});# fix for some misconfigured tok2-servers
	}
	elsif($ENV{'SERVER_NAME'}=~m/\.h(ut)?\d+?\.ru/){
		$H{end_html}.='<div style="display:none"><noembed><xml><xmp>';
	}
}

######################################################################
# Initial Superuser Setup
######################################################################

sub send_init{
	my $result=create_files();
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	print qq|</head>$H{begin_body}<center><h2>LE&nbsp;CHAT - $I{initsetup}</h2>|;
	print qq|<table width=50><form action="$S" method="post"><input type="hidden" name="action" value="init"></tr></td><tr><td align=center><h3>$I{setsu}</h3><table><tr><td>$I{setsunick}</td><td><input type="text" name="sunick" size="15"></td></tr><tr><td>$I{setsupass}</td><td><input type="text" name="supass" size="15"></td></tr><tr><td>$I{setsupassconf}</td><td><input type="text" name="supassc" size="15"></td></tr></table><br><br></tr></td><tr><td align="left">$I{setsuhelp}</tr></td><tr><td align="center">|;
	print qq|<h3>$I{initback}</h3></tr></td><tr><td align="left">$I{initbackhelp}<br></td></tr><tr><td align="center"><textarea name="backupdata" rows="8" cols="80" wrap="off">$result</textarea><br><br><br></td></tr><tr><td align="center"><tr><td align="center"><br><input type="submit" value="$I{initbut}"></form></td></tr></table><br>|;
	print qq|<small>LE&nbsp;CHAT&nbsp;-&nbsp;$version</small></center>$H{end_body}$H{end_html}|;
	exit;
}

sub create_files{
	my $result='';
	# create directories if needed
	my @dirs=split(/\//,$datadir);my $dir='';
	while($_=shift@dirs){$dir.=$_;mkdir($dir,0700) unless -d$dir;$dir.='/'}
	chmod(0700,$datadir);
	# create files, keep existing ones
	unless(-e"$datadir/config"){sysopen(CONFIG,"$datadir/config",O_RDWR|O_CREAT,0600);close(CONFIG)}
	unless(-e"$datadir/members"){sysopen(MEMBERS,"$datadir/members",O_RDWR|O_CREAT,0600);close(MEMBERS)}
	unless(-e"$datadir/sessions"){sysopen(SESSIONS,"$datadir/sessions",O_RDWR|O_CREAT,0600);close(SESSIONS)}
	unless(-e"$datadir/messages"){sysopen(MESSAGES,"$datadir/messages",O_RDWR|O_CREAT,0600);close(MESSAGES)}
	unless(-e"$datadir/waiting"){sysopen(WAITING,"$datadir/waiting",O_RDWR|O_CREAT,0600);close(WAITING)}
	# check initial data in lechat.txt
	if(-e'./lechat.txt'){
		my $backupdata='';
		sysopen(LECHAT,'./lechat.txt',O_RDONLY) or send_fatal("$I{errfile} (lechat.txt/open)");
		flock(LECHAT,LOCK_SH) or send_fatal("$I{errfile} (lechat.txt/lock)");
		while(<LECHAT>){$backupdata.=$_};
		close(LECHAT);
		$result="Results of lechat.txt:\n".get_restore_results($backupdata);
		unlink('./lechat.txt');
		load_config();
	}
	return $result;
}

sub init_chat{
	# restore backups if given
	my $restore=$I{invalidbackup};
	$restore=get_restore_results() if $Q{backupdata}[0];
	$restore=~s/\n/<br>/g;
	# write superuser into "admin"
	my $suwrite=$I{suerrunknown};
	my $sudata='+';my $suverify='-';
	if(-e"$datadir/admin"){
		$suwrite=$I{suerrfileexist};
	}elsif(!valid_nick($Q{sunick}[0])){
		$suwrite=$I{suerrbadnick};
	}elsif(!valid_pass($Q{supass}[0])){
		$suwrite=$I{suerrbadpass};
	}elsif($Q{supass}[0]ne$Q{supassc}[0]){
		$suwrite=$I{suerrbadpassc};
	}else{# all good data here
		$sudata=hash_this($Q{sunick}[0].hash_this($Q{sunick}[0]).hash_this($Q{supass}[0]).$Q{supass}[0]);
		sysopen(ADMIN,"$datadir/admin",O_RDWR|O_CREAT,0600) or send_fatal("$I{errfile} (admin/open)");
		flock(ADMIN,LOCK_EX) or send_fatal("$I{errfile} (admin/lock)");
		print ADMIN $sudata;
		close(ADMIN);
		# read and verify data
		sysopen(ADMIN,"$datadir/admin",O_RDONLY,0600) or unlink("$datadir/admin") and send_fatal("$I{errfile} (admin/open)");
		flock(ADMIN,LOCK_EX) or unlink("$datadir/admin") and send_fatal("$I{errfile} (admin/lock)");
		$suverify=<ADMIN>;
		close(ADMIN);
		if($sudata eq $suverify){
			$suwrite=$I{suwritesucc};
		}else{# delete again if not written correctly
			unlink("$datadir/admin");
			$suwrite=$I{suwritefail};
		}
	}
	# Print results:
	print qq|$H{begin_html}<head>$H{meta_html}|;
	print_stylesheet('admin');
	print qq|</head>$H{begin_body}<center><h2>LE&nbsp;CHAT - $I{initsetup}</h2><br>|;
	print qq|<h3>$I{setsu}</h3>$suwrite<br><br><br>|;
	print qq|<h3>$I{initback}</h2>$restore<br><br><br>|;
	print qq|<form action="$S" method="post"><input type="hidden" name="action" value="setup">|;
	print qq|<input type="hidden" name="name" value="$Q{sunick}[0]">|;
	print qq|<input type="hidden" name="pass" value="$Q{supass}[0]">|;
	print qq|<input type="submit" value="$I{initgotosetup}"></form><br>|;
	print qq|<small>LE&nbsp;CHAT&nbsp;-&nbsp;$version</small></center>$H{end_body}$H{end_html}|;
	exit;
}

######################################################################
# guest access handling
######################################################################

sub set_guests_access{
	if($_[0]==0){unlink("$datadir/guests1","$datadir/guests2","$datadir/guests3")};
	if($_[0]==3){unlink("$datadir/guests1","$datadir/guests2");sysopen(GUESTS,"$datadir/guests3",O_RDWR|O_CREAT,0600);close(GUESTS)};
	if($_[0]==2){unlink("$datadir/guests1","$datadir/guests3");sysopen(GUESTS,"$datadir/guests2",O_RDWR|O_CREAT,0600);close(GUESTS)};
	if($_[0]==1){unlink("$datadir/guests2","$datadir/guests3");sysopen(GUESTS,"$datadir/guests1",O_RDWR|O_CREAT,0600);close(GUESTS)};
	$guests=get_guests_access();
}

sub get_guests_access{
	return 3 if -e"$datadir/guests3";
	return 2 if -e"$datadir/guests2";
	return 1 if -e"$datadir/guests1";
	return 0;
}

######################################################################
# this and that
######################################################################

sub suspend_chat{unlink("$datadir/opened");$C{chataccess}=-e"$datadir/opened"}
sub unsuspend_chat{sysopen(SUSP,"$datadir/opened",O_RDWR|O_CREAT,0600);close(SUSP);$C{chataccess}=-e"$datadir/opened";}
sub expiredm{($^T-$_[0]>60*$C{messageexpire})}
sub expireds{($^T-$_[0]>60*($_[1]>1?$C{sessionexpire}:$C{guestsexpire}))}
sub expiredw{($^T-$_[0]>60*$C{waitingexpire})}
sub valid_nick{!($_[0]!~/^.{1,$C{maxname}}$/ or $_[0]=~/[^\w\d\s\(\)\[\]\{\}\=\/\-\!\@\#\$\%\?\+\*\^\.]/g or $_[0]!~/[a-z0-9]/i)}
sub valid_pass{($_[0]=~/^.{$C{minpass},}$/)}
sub similar_nick{my $x=lc($_[0]);my $y=lc($_[1]);$x=~y/a-z0-9//cd;$y=~y/a-z0-9//cd;$x eq $y?1:0}
sub hash_this{require Digest::MD5;Digest::MD5->import(qw(md5_hex));return md5_hex($_[0])}
sub get_timestamp{$_[0]=$^T unless $_[0];my($sec,$min,$hour,$day,$mon,$year)=gmtime($_[0]);$year+=1900;$mon++;foreach($sec,$min,$hour,$day,$mon){$_=substr('0'.$_,-2,2)}return"$year-$mon-$day $hour:$min:$sec"}

sub get_timeout{ # lastpost, status
	my $s=$_[0]+(60*($_[1]>1?$C{sessionexpire}:$C{guestsexpire}))-$^T;
	my $m=int($s/60);$s-=$m*60;
	my $h=int($m/60);$m-=$h*60;
	$s=substr('0'.$s,-2,2);
	$m=substr('0'.$m,-2,2)if$h;
	return $h?"$h:$m:$s":"$m:$s";
}

sub print_colours{
	# Prints a list with selected named HTML colours and filters out illegible text colours for the given background.
	# It's a simple comparison of weighted grey values. This is not very accurate but gets the job done well enough.
	# If you want more accuracy, do some research about "Delta E", though the serious math involved there is not worth the effort just for this here I guess. ;)
	my %colours=(# short selection of some HTML named colours:
		Beige=>'F5F5DC',Black=>'000000',Blue=>'0000FF',BlueViolet=>'8A2BE2',Brown=>'A52A2A',Cyan=>'00FFFF',DarkBlue=>'00008B',DarkGreen=>'006400',DarkRed=>'8B0000',DarkViolet=>'9400D3',
		DeepSkyBlue=>'00BFFF',Gold=>'FFD700',Grey=>'808080',Green=>'008000',HotPink=>'FF69B4',Indigo=>'4B0082',LightBlue=>'ADD8E6',LightGreen=>'90EE90',LimeGreen=>'32CD32',
		Magenta=>'FF00FF',Olive=>'808000',Orange=>'FFA500',OrangeRed=>'FF4500',Purple=>'800080',Red=>'FF0000',RoyalBlue=>'4169E1',SeaGreen=>'2E8B57',Sienna=>'A0522D',
		Silver=>'C0C0C0',Tan=>'D2B48C',Teal=>'008080',Violet=>'EE82EE',White=>'FFFFFF',Yellow=>'FFFF00',YellowGreen=>'9ACD32'
	);
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
	  $fstyle.="color:$fcolour;" if $fcolour;
	  $fstyle.="font-family:$sface;" if $sface;
	  $fstyle.='font-size:smaller;' if $fsmall;
	  $fstyle.='font-style:italic;' if $fitalic;
	  $fstyle.='font-weight:bold;' if $fbold;
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
	  $fstyle.="color:$fcolour;" if $fcolour;
	  $fstyle.="font-family:$sface;" if $sface;
	  $fstyle.='font-size:smaller;' if $fsmall;
	  $fstyle.='font-style:italic;' if $fitalic;
	  $fstyle.='font-weight:bold;' if $fbold;
	my $fstart=q|<font|;
	  $fstart.=qq| color="$fcolour"|if $fcolour;
	  $fstart.=qq| face="$fface"|if $fface;
	  $fstart.=qq| size="-1"|if $fsmall;
	  $fstart.=qq| style="$fstyle"| if $fstyle;
	  $fstart.=q|>|;
	  $fstart.='<b>' if $fbold;
	  $fstart.='<i>' if $fitalic;
	my $fend='';
	  $fend.='</i>' if $fitalic;
	  $fend.='</b>' if $fbold;
	  $fend.='</font>';
	return "$fstart$text$fend";
}

######################################################################
# cgi stuff
######################################################################
sub GetQuery{my($qs,$qn,$qv,%qh);read(STDIN,$qs,$ENV{'CONTENT_LENGTH'});my @split=split(/&/,$qs);foreach(@split){($qn,$qv)=split(/=/,$_);$qv=~tr/+/ /;$qv=~s/%([\dA-Fa-f]{2})/pack("C",hex($1))/eg;$qh{$qn}=[] unless $qh{$qn};push @{$qh{$qn}},$qv}return %qh}
sub GetParam{my($ps,$pn,$pv,%ph);$ps=$ENV{'QUERY_STRING'};my @split=split(/&/,$ps);foreach(@split){($pn,$pv)=split(/=/,$_);$pv=~tr/+/ /;$pv=~s/%([\dA-Fa-f]{2})/pack("C",hex($1))/eg;$ph{$pn}=[] unless $ph{$pn};push @{$ph{$pn}},$pv}return %ph}
sub GetScript{if($0=~/[^\\\/]+$/){return $&}else{die}}

__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBUEkMUcr7q1ZyCqQiEQI5tgCg74J6uU86bTk8baVFDwLclRARTc0An0Ng
pPGM1JsZLflu8qqoBVsSATMC
=XIKl
-----END PGP SIGNATURE-----
