import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Service layer (hexagonal port adapter shape): creates bookings. */
public class BookingService {
    private final Map<String, String> store = new HashMap<>();

    public String createBooking(String customer, String slot) {
        String id = "bk_" + UUID.randomUUID().toString().substring(0, 8);
        store.put(id, customer + "|" + slot);
        return id;
    }

    public String findBooking(String id) {
        return store.get(id);
    }

    public int count() {
        return store.size();
    }
}
