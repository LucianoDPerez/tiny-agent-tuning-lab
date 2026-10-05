/** Executable check: idempotent create must not duplicate. Run: javac *.java && java Main */
public class Main {
    public static void main(String[] args) {
        BookingService svc = new BookingService();
        String key = "idem-key-1";
        String first = svc.createBooking("ana", "10:00");
        String second = svc.createBooking("ana", "10:00");
        // After the fix, calling with the same idempotency key must return
        // the SAME booking id and keep count at 1. Update this check accordingly.
        System.out.println("count=" + svc.count());
        System.out.println(first.equals(second) && svc.count() == 1 ? "PASS" : "FAIL");
    }
}
