// Trap Or Value - localStorage interop functions
window.trapValueStorage = {
    KEY: "trapvalue_played_snapshots",
    MAX_IDS: 1000,

    getPlayedIds: function () {
        try {
            const data = localStorage.getItem(this.KEY);
            if (!data) return [];
            const ids = JSON.parse(data);
            return Array.isArray(ids) ? ids : [];
        } catch (e) {
            console.warn("Failed to parse played IDs from localStorage:", e);
            return [];
        }
    },

    savePlayedId: function (id) {
        try {
            let ids = this.getPlayedIds();
            if (!ids.includes(id)) {
                ids.push(id);
                // Enforce maximum limit - remove oldest entries (FIFO)
                if (ids.length > this.MAX_IDS) {
                    ids = ids.slice(ids.length - this.MAX_IDS);
                }
                localStorage.setItem(this.KEY, JSON.stringify(ids));
            }
            return true;
        } catch (e) {
            console.error("Failed to save played ID:", e);
            return false;
        }
    },

    clearPlayedIds: function () {
        try {
            localStorage.removeItem(this.KEY);
            return true;
        } catch (e) {
            console.error("Failed to clear played IDs:", e);
            return false;
        }
    },

    getCount: function () {
        return this.getPlayedIds().length;
    }
};
