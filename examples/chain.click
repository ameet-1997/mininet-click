// 3 h0 h0-eth0 10.0.0.1 <-> s1-eth4 92:a9:86:0e:78:56 22:29:d0:ef:c6:95
// 3 h1 h1-eth0 10.0.0.2 <-> s1-eth4 7e:59:e5:bc:20:5f 22:29:d0:ef:c6:95
// 3 h2 h2-eth0 10.0.0.3 <-> s1-eth4 fa:e4:33:81:9a:18 22:29:d0:ef:c6:95
// 0 h3 h3-eth0 10.0.0.4 <-> s1-eth1 46:a0:10:37:ed:17 02:2a:ad:11:3f:90
// 1 h4 h4-eth0 10.0.0.5 <-> s1-eth2 06:63:ac:6d:b5:51 a2:f0:bd:33:23:09
// 2 h5 h5-eth0 10.0.0.6 <-> s1-eth3 4e:be:8f:f6:ef:2a c6:41:85:5b:d1:04
// 4 h6 h6-eth0 10.0.0.7 <-> s1-eth5 4a:8f:3e:69:82:34 d6:b5:f0:90:b9:01
// 4 h7 h7-eth0 10.0.0.8 <-> s1-eth5 6e:b1:d2:09:72:7b d6:b5:f0:90:b9:01
// 4 h8 h8-eth0 10.0.0.9 <-> s1-eth5 d6:8d:5c:d7:75:dc d6:b5:f0:90:b9:01
// 3 s0 s0-eth4 None <-> s1-eth4 06:39:53:52:1a:d5 22:29:d0:ef:c6:95
// 4 s2 s2-eth4 None <-> s1-eth5 02:1d:f0:cd:61:50 d6:b5:f0:90:b9:01

c0 :: Classifier(12/0806 20/0001, 12/0806 20/0002, 12/0800, -);

FromDevice('s1-eth1')
-> Print(got0)
-> Paint(0)
-> [0]c0;

FromDevice('s1-eth2')
-> Print(got1)
-> Paint(1)
-> [0]c0;

FromDevice('s1-eth3')
-> Print(got2)
-> Paint(2)
-> [0]c0;

FromDevice('s1-eth4')
-> Print(got3)
-> Paint(3)
-> [0]c0;

FromDevice('s1-eth5')
-> Print(got4)
-> Paint(4)
-> [0]c0;

out0 :: Queue(8)
-> Print(out0)
-> ToDevice('s1-eth1');

out1 :: Queue(8)
-> Print(out1)
-> ToDevice('s1-eth2');

out2 :: Queue(8)
-> Print(out2)
-> ToDevice('s1-eth3');

out3 :: Queue(8)
-> Print(out3)
-> ToDevice('s1-eth4');

out4 :: Queue(8)
-> Print(out4)
-> ToDevice('s1-eth5');

c0[0] -> arpt :: Tee(5);

arpt[0]
-> CheckPaint(0)
-> Print(arp_req_from0)
-> ARPResponder(
  10.0.0.1 02:2a:ad:11:3f:90,
  10.0.0.2 02:2a:ad:11:3f:90,
  10.0.0.3 02:2a:ad:11:3f:90,
  10.0.0.4 02:2a:ad:11:3f:90,
  10.0.0.5 02:2a:ad:11:3f:90,
  10.0.0.6 02:2a:ad:11:3f:90,
  10.0.0.7 02:2a:ad:11:3f:90,
  10.0.0.8 02:2a:ad:11:3f:90,
  10.0.0.9 02:2a:ad:11:3f:90)
-> Print(arp_response)
-> out0;

arpt[1]
-> CheckPaint(1)
-> Print(arp_req_from1)
-> ARPResponder(
  10.0.0.1 a2:f0:bd:33:23:09,
  10.0.0.2 a2:f0:bd:33:23:09,
  10.0.0.3 a2:f0:bd:33:23:09,
  10.0.0.4 a2:f0:bd:33:23:09,
  10.0.0.5 a2:f0:bd:33:23:09,
  10.0.0.6 a2:f0:bd:33:23:09,
  10.0.0.7 a2:f0:bd:33:23:09,
  10.0.0.8 a2:f0:bd:33:23:09,
  10.0.0.9 a2:f0:bd:33:23:09)
-> Print(arp_response)
-> out1;

arpt[2]
-> CheckPaint(2)
-> Print(arp_req_from2)
-> ARPResponder(
  10.0.0.1 c6:41:85:5b:d1:04,
  10.0.0.2 c6:41:85:5b:d1:04,
  10.0.0.3 c6:41:85:5b:d1:04,
  10.0.0.4 c6:41:85:5b:d1:04,
  10.0.0.5 c6:41:85:5b:d1:04,
  10.0.0.6 c6:41:85:5b:d1:04,
  10.0.0.7 c6:41:85:5b:d1:04,
  10.0.0.8 c6:41:85:5b:d1:04,
  10.0.0.9 c6:41:85:5b:d1:04)
-> Print(arp_response)
-> out2;

arpt[3]
-> CheckPaint(3)
-> Print(arp_req_from3)
-> ARPResponder(
  10.0.0.1 22:29:d0:ef:c6:95,
  10.0.0.2 22:29:d0:ef:c6:95,
  10.0.0.3 22:29:d0:ef:c6:95,
  10.0.0.4 22:29:d0:ef:c6:95,
  10.0.0.5 22:29:d0:ef:c6:95,
  10.0.0.6 22:29:d0:ef:c6:95,
  10.0.0.7 22:29:d0:ef:c6:95,
  10.0.0.8 22:29:d0:ef:c6:95,
  10.0.0.9 22:29:d0:ef:c6:95)
-> Print(arp_response)
-> out3;

arpt[4]
-> CheckPaint(4)
-> Print(arp_req_from4)
-> ARPResponder(
  10.0.0.1 d6:b5:f0:90:b9:01,
  10.0.0.2 d6:b5:f0:90:b9:01,
  10.0.0.3 d6:b5:f0:90:b9:01,
  10.0.0.4 d6:b5:f0:90:b9:01,
  10.0.0.5 d6:b5:f0:90:b9:01,
  10.0.0.6 d6:b5:f0:90:b9:01,
  10.0.0.7 d6:b5:f0:90:b9:01,
  10.0.0.8 d6:b5:f0:90:b9:01,
  10.0.0.9 d6:b5:f0:90:b9:01)
-> Print(arp_response)
-> out4;

c0[1] -> Discard;

c0[3] -> Discard;

rt :: StaticIPLookup(
  10.0.0.1/32 3,
  10.0.0.2/32 3,
  10.0.0.3/32 3,
  10.0.0.4/32 0,
  10.0.0.5/32 1,
  10.0.0.6/32 2,
  10.0.0.7/32 4,
  10.0.0.8/32 4,
  10.0.0.9/32 4);

c0[2]
-> Print(ip_req)
-> Strip(14)
-> Print(stripped)
-> CheckIPHeader
-> GetIPAddress(16)
-> Print(ip)
-> [0]rt;

rt[0]
-> Print(out0)
-> EtherEncap(0x0800, 02:2a:ad:11:3f:90, 46:a0:10:37:ed:17)
-> Print(ether)
-> out0;

rt[1]
-> Print(out1)
-> EtherEncap(0x0800, a2:f0:bd:33:23:09, 06:63:ac:6d:b5:51)
-> Print(ether)
-> out1;

rt[2]
-> Print(out2)
-> EtherEncap(0x0800, c6:41:85:5b:d1:04, 4e:be:8f:f6:ef:2a)
-> Print(ether)
-> out2;

rt[3]
-> Print(out3)
-> EtherEncap(0x0800, 22:29:d0:ef:c6:95, 06:39:53:52:1a:d5)
-> Print(ether)
-> out3;

rt[4]
-> Print(out4)
-> EtherEncap(0x0800, d6:b5:f0:90:b9:01, 02:1d:f0:cd:61:50)
-> Print(ether)
-> out4;

