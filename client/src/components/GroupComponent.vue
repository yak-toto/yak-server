<template>
  <div class="columns">
    <div class="column is-2">
      <GroupNavbar />
    </div>
    <div class="column">
      <h3 class="title">Groupe {{ $route.params.groupName }}</h3>
      <div class="box">
        <form v-on:submit.prevent="postGroup">
          <div class="table-container">
            <table class="table is-fullwidth is-striped">
              <tr v-for="match in groupResource">
                <td>{{ match["results"][0]["team"] }}</td>
                <td>
                  <input class="input is-small" min="0" type="number" v-model="match['results'][0]['score']">
                </td>
                <td>
                  <input class="input is-small" min="0" type="number" v-model="match['results'][1]['score']">
                </td>
                <td>{{ match["results"][1]["team"] }}</td>
              </tr>
            </table>
          </div>
          <div>
            <button class="button is-dark">Valider</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import GroupNavbar from './GroupNavbar.vue';

export default {
  name: 'GroupComponent',
  components: {
    GroupNavbar,
  },
  data() {
    return {
      groupResource: [],
    };
  },
  methods: {
    getGroup() {
      this.$store.dispatch('getGroup', { groupName: this.$route.params.groupName })
        .then((res) => {
          this.groupResource = res.data;
        });
    },
    postGroup() {
      for (let index = 0; index < this.groupResource.length; index += 1) {
        this.$store.dispatch('postMatch', { matchId: this.groupResource[index].id, matchResource: this.groupResource[index] });
      }
    },
  },
  beforeRouteUpdate(to, from, next) {
    if (!this.$store.getters.isAuthenticated) {
      this.$store.dispatch('logout');
      next('/login');
    } else {
      next();
      this.getGroup();
    }
  },
  created() {
    this.$watch(
      () => this.$route.params,
      () => {
        if (this.$route.params.groupName) {
          this.getGroup();
        }
      },
      { immediate: true },
    );
  },
};

</script>
