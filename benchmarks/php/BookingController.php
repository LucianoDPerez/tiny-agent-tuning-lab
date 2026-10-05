<?php
// Laravel-style controller shape (framework-free fixture).
class BookingController
{
    private array $store = [];

    public function store(array $input): array
    {
        $id = 'bk_' . substr(md5(uniqid('', true)), 0, 8);
        $this->store[$id] = $input;
        return ['status' => 201, 'id' => $id];
    }

    public function show(string $id): array
    {
        if (!isset($this->store[$id])) {
            return ['status' => 404, 'error' => 'not found'];
        }
        return ['status' => 200, 'booking' => $this->store[$id]];
    }
}
