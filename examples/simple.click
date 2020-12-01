// Example configuration generated for a 3 node/1 switch topology.
// The configuration is generated in click.py (see `def router`).
//
// 0 h0-eth0 10.0.0.1 de:87:63:76:0c:af <-> 56:b4:e2:25:43:e1 s0-eth1
// 1 h1-eth0 10.0.0.2 26:c0:11:54:cd:a7 <-> 66:40:2d:f6:ce:3b s0-eth2
// 2 h2-eth0 10.0.0.3 66:b8:e4:78:c5:2a <-> aa:e6:6b:83:66:5e s0-eth3

c0 :: Classifier(12/0806 20/0001, 12/0806 20/0002, 12/0800, -);

FromDevice('s0-eth1')
-> Print(got0)
-> Paint(0)
-> [0]c0;

FromDevice('s0-eth2')
-> Print(got1)
-> Paint(1)
-> [0]c0;

FromDevice('s0-eth3')
-> Print(got2)
-> Paint(2)
-> [0]c0;

out0 :: Queue(8)
-> Print(out0)
-> ToDevice('s0-eth1');

out1 :: Queue(8)
-> Print(out1)
-> ToDevice('s0-eth2');

out2 :: Queue(8)
-> Print(out2)
-> ToDevice('s0-eth3');

c0[0] -> arpt :: Tee(3);

arpt[0]
-> CheckPaint(0)
-> Print(arp_req_from0)
-> ARPResponder(
  10.0.0.1 56:b4:e2:25:43:e1,
  10.0.0.2 56:b4:e2:25:43:e1,
  10.0.0.3 56:b4:e2:25:43:e1)
-> Print(arp_response)
-> out0;

arpt[1]
-> CheckPaint(1)
-> Print(arp_req_from1)
-> ARPResponder(
  10.0.0.1 66:40:2d:f6:ce:3b,
  10.0.0.2 66:40:2d:f6:ce:3b,
  10.0.0.3 66:40:2d:f6:ce:3b)
-> Print(arp_response)
-> out1;

arpt[2]
-> CheckPaint(2)
-> Print(arp_req_from2)
-> ARPResponder(
  10.0.0.1 aa:e6:6b:83:66:5e,
  10.0.0.2 aa:e6:6b:83:66:5e,
  10.0.0.3 aa:e6:6b:83:66:5e)
-> Print(arp_response)
-> out2;

c0[1] -> Discard;

c0[3] -> Discard;

rt :: StaticIPLookup(
  10.0.0.1/32 0,
  10.0.0.2/32 1,
  10.0.0.3/32 2);

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
-> EtherEncap(0x0800, 56:b4:e2:25:43:e1, de:87:63:76:0c:af)
-> Print(ether)
-> out0;

rt[1]
-> Print(out1)
-> EtherEncap(0x0800, 66:40:2d:f6:ce:3b, 26:c0:11:54:cd:a7)
-> Print(ether)
-> out1;

rt[2]
-> Print(out2)
-> EtherEncap(0x0800, aa:e6:6b:83:66:5e, 66:b8:e4:78:c5:2a)
-> Print(ether)
-> out2;

