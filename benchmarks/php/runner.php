<?php
require __DIR__ . '/BookingController.php';

$c = new BookingController();
// After the fix, invalid input (missing customer/slot) must return
// ['status' => 400, ...] instead of 201. Valid input keeps working.
$bad = $c->store([]);
$good = $c->store(['customer' => 'ana', 'slot' => '10:00']);
$ok = ($bad['status'] === 400) && ($good['status'] === 201);
echo $ok ? "PASS\n" : "FAIL\n";
exit($ok ? 0 : 1);
